from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import Plant, PlantCompound, Compound, CompoundActivity, Activity, CompoundTarget, Target
from typing import Optional
from pydantic import BaseModel, Field, model_validator
import re

router = APIRouter(prefix='/discovery', tags=['therapeutic-candidate-discovery'])

class DiscoveryRequest(BaseModel):
    condition_name: Optional[str] = Field(default=None, min_length=2)
    condition_type: Optional[str] = None
    symptoms_or_features: Optional[str] = None
    molecular_features: Optional[str] = None
    structure_description: Optional[str] = None
    sequence_or_marker: Optional[str] = None

    @model_validator(mode='after')
    def require_some_condition_information(self):
        values = [self.condition_name, self.condition_type, self.symptoms_or_features,
                  self.molecular_features, self.structure_description, self.sequence_or_marker]
        if not any(v and v.strip() for v in values):
            raise ValueError('Provide a disease/virus name or at least one biological, molecular, structural, or sequence/marker clue.')
        return self

# Transparent concept maps make the prediction auditable. This is an AI-assisted
# pattern-ranking prototype, not a clinical model or a claim of treatment efficacy.
ACTIVITY_CONCEPTS = {
    'anti-inflammatory': {'inflammation','inflammatory','inflammation-related','arthritis','swelling','colitis','pain','edema','cytokine','immune','nf-kb','nfkb'},
    'antioxidant': {'oxidative','oxidative stress','free radical','redox','reactive oxygen','ros'},
    'antimicrobial': {'bacteria','bacterial','microbial','infection','infectious','fungal','fungus','pathogen','microorganism','virus','viral','antimicrobial'},
    'insecticidal': {'insect','mosquito','pest','vector','larva','larvae','arthropod'},
    'antifeedant': {'insect','pest','feeding','crop pest'},
}

CONDITION_EXPANSIONS = {
    'cancer': {'tumor','tumour','neoplasm','oncology','proliferation','apoptosis','inflammation','oxidative','cytokine'},
    'viral': {'virus','viral','infection','pathogen','antimicrobial'},
    'bacterial': {'bacteria','bacterial','infection','pathogen','antimicrobial'},
    'fungal': {'fungus','fungal','infection','pathogen','antimicrobial'},
    'inflammatory': {'inflammation','inflammatory','immune','cytokine','nf-kb','nfkb'},
    'neurodegenerative': {'oxidative','inflammation','neuroinflammation','redox','neuronal'},
    'diabetes': {'oxidative','inflammation','metabolic','glucose','insulin'},
    'arthritis': {'inflammation','inflammatory','pain','swelling','immune'},
    'respiratory': {'inflammation','infection','viral','bacterial','oxidative'},
    'skin': {'inflammation','infection','antimicrobial','oxidative','wound'},
    'wound': {'inflammation','infection','oxidative','repair'},
}

def tokens(text: str):
    return set(re.findall(r'[a-z0-9][a-z0-9_-]+', (text or '').lower()))

def normalized_text(text: str):
    return re.sub(r'[^a-z0-9_-]+', ' ', (text or '').lower())

def query_concepts(text: str):
    low = normalized_text(text)
    q = tokens(text)
    expanded = set(q)
    for trigger, additions in CONDITION_EXPANSIONS.items():
        if trigger in q or trigger in low:
            expanded.update(additions)
    return expanded

def concept_hits(activity: str, qtokens):
    concepts = ACTIVITY_CONCEPTS.get(activity.lower(), set())
    return sorted(x for x in concepts if x in qtokens)

def target_hits(target_text: str, qtokens):
    low = normalized_text(target_text)
    return sorted({tok for tok in qtokens if len(tok) > 3 and tok in low})

def pattern_label(aligned_activities, composition):
    acts = [a for a in aligned_activities[:2]]
    if len(acts) >= 2:
        return ' + '.join(acts)
    if len(acts) == 1:
        return acts[0]
    if composition:
        return 'compound-composition signal'
    return 'insufficient evidence pattern'

def confidence_label(score):
    if score >= 70: return 'High pattern strength'
    if score >= 45: return 'Moderate pattern strength'
    if score >= 20: return 'Exploratory pattern'
    return 'Low / insufficient pattern'

@router.post('/match')
async def therapeutic_candidate_discovery(payload: DiscoveryRequest, db: AsyncSession = Depends(get_db)):
    query_parts = [payload.condition_name, payload.condition_type, payload.symptoms_or_features,
                   payload.molecular_features, payload.structure_description, payload.sequence_or_marker]
    query = ' '.join(x for x in query_parts if x)
    qtokens = query_concepts(query)

    rows = (await db.execute(
        select(Plant, Compound, Activity, Target)
        .join(PlantCompound, PlantCompound.plant_id == Plant.plant_id, isouter=True)
        .join(Compound, Compound.compound_id == PlantCompound.compound_id, isouter=True)
        .join(CompoundActivity, CompoundActivity.compound_id == Compound.compound_id, isouter=True)
        .join(Activity, Activity.activity_id == CompoundActivity.activity_id, isouter=True)
        .join(CompoundTarget, CompoundTarget.compound_id == Compound.compound_id, isouter=True)
        .join(Target, Target.target_id == CompoundTarget.target_id, isouter=True)
    )).all()

    grouped = {}
    for plant, compound, activity, target in rows:
        g = grouped.setdefault(plant.plant_id, {
            'plant': plant, 'compounds': {}, 'activities': set(), 'targets': set(), 'compound_details': {}
        })
        if compound:
            cd = g['compound_details'].setdefault(compound.compound_id, {
                'name': compound.preferred_name, 'activities': set(), 'targets': set(),
                'mw': compound.molecular_weight, 'xlogp': compound.xlogp, 'formula': compound.molecular_formula
            })
            g['compounds'][compound.compound_id] = compound.preferred_name
            if activity:
                cd['activities'].add(activity.name)
            if target:
                cd['targets'].add(' '.join(x for x in [target.target_name, target.gene_symbol, target.description] if x))
        if activity:
            g['activities'].add(activity.name)
        if target:
            g['targets'].add(' '.join(x for x in [target.target_name, target.gene_symbol, target.description] if x))

    ranked = []
    for g in grouped.values():
        p = g['plant']
        acts = sorted(g['activities'])
        targets = sorted(g['targets'])
        compounds = sorted(g['compounds'].values())
        plant_text = ' '.join([
            p.common_name, p.scientific_name, p.family or '', p.description or '',
            p.traditional_relevance or '', p.reported_biological_activities or '',
            p.phytochemical_information or '', *acts, *targets, *compounds
        ]).lower()

        activity_points = 0.0
        composition_points = 0.0
        target_points = 0.0
        profile_points = 0.0
        evidence_points = 0.0
        reasons = []
        aligned_activities = []
        scored_compounds = []

        for cid, cd in g['compound_details'].items():
            cscore = 0.0
            c_reasons = []
            c_hits = set()
            for act in sorted(cd['activities']):
                hits = concept_hits(act, qtokens)
                if hits:
                    cscore += 32 + 4 * min(3, len(hits))
                    c_hits.update(hits)
                    c_reasons.append(f'{act}: {", ".join(hits[:3])}')
            compound_target_hits = sorted({h for t in cd['targets'] for h in target_hits(t, qtokens)})
            if compound_target_hits:
                cscore += min(15, len(compound_target_hits) * 5)
                c_reasons.append('target-context overlap')
            if cd['mw'] is not None: cscore += 2
            if cd['formula']: cscore += 1
            if cscore > 0:
                scored_compounds.append({
                    'name': cd['name'], 'score': round(cscore, 1),
                    'activities': sorted(cd['activities']), 'targets': sorted(cd['targets'])[:5],
                    'molecular_weight': cd['mw'], 'formula': cd['formula'],
                    'matched_signals': sorted(c_hits | set(compound_target_hits)),
                    'reasons': c_reasons[:3]
                })

        for act in acts:
            hits = concept_hits(act, qtokens)
            if hits:
                aligned_activities.append((act, hits))

        # Weighted evidence channels sum to a 0-100 research-priority score.
        if aligned_activities:
            activity_points = min(45, 22 * len(aligned_activities) + 4 * min(3, len({h for _,hs in aligned_activities for h in hs})))
            reasons.append(f'{len(aligned_activities)} reported activity pattern(s) align with the query')

        if scored_compounds:
            scored_compounds.sort(key=lambda x: x['score'], reverse=True)
            best_c = scored_compounds[0]['score']
            composition_points = min(25, best_c * 0.45 + min(8, len(scored_compounds) * 2))
            reasons.append(f'{len(scored_compounds)} compound composition signal(s) support the pattern')

        all_target_hits = sorted({h for t in targets for h in target_hits(t, qtokens)})
        if all_target_hits:
            target_points = min(15, 5 * len(all_target_hits))
            reasons.append(f'target context overlaps query signals: {", ".join(all_target_hits[:4])}')

        profile_overlap = sum(1 for tok in qtokens if len(tok) > 3 and tok in plant_text)
        if profile_overlap:
            profile_points = min(10, profile_overlap * 1.5)
            reasons.append(f'{profile_overlap} query-pattern term(s) occur in the plant profile')

        evidence_flags = [bool(acts), bool(compounds), bool(targets), bool(p.taxonomy_id), bool(p.family), bool(p.description)]
        evidence_points = round(5 * sum(evidence_flags) / len(evidence_flags), 1)

        score = round(min(100, activity_points + composition_points + target_points + profile_points + evidence_points), 1)
        scored_compounds.sort(key=lambda x: x['score'], reverse=True)
        aligned_names = [x[0] for x in sorted(aligned_activities, key=lambda z: len(z[1]), reverse=True)]
        pattern = pattern_label(aligned_names, scored_compounds)
        conf = confidence_label(score)
        best_compound = scored_compounds[0]['name'] if scored_compounds else None
        recommendation = (
            f'Research priority: investigate {p.common_name} for the {pattern} pattern'
            + (f', with {best_compound} as the leading composition signal.' if best_compound else '.')
        )

        ranked.append({
            'plant_id': p.plant_id,
            'plant': p.common_name,
            'scientific_name': p.scientific_name,
            'score': score,
            'pattern': pattern,
            'confidence_label': conf,
            'prediction': recommendation,
            'signal_breakdown': {
                'activity_alignment': round(activity_points, 1),
                'compound_composition': round(composition_points, 1),
                'target_context': round(target_points, 1),
                'profile_pattern_overlap': round(profile_points, 1),
                'evidence_completeness': evidence_points,
            },
            'matched_signals': sorted({h for _,hs in aligned_activities for h in hs} | set(all_target_hits))[:10],
            'promising_composition': scored_compounds[:3],
            'compounds': compounds,
            'activities': acts,
            'targets': targets[:6],
            'evidence': 'reported database associations' if (acts or targets or compounds) else 'plant profile only',
            'reasons': reasons[:5]
        })

    ranked.sort(key=lambda x: (x['score'], len(x['promising_composition']), len(x['activities'])), reverse=True)
    top = [x for x in ranked if x['score'] > 0][:10]
    if not top:
        top = [x for x in ranked if x['promising_composition'] or x['activities']][:10]

    # Complementary patterns are framed strictly as research hypotheses.
    combo = []
    seen_patterns = set()
    for item in top:
        if item['pattern'] not in seen_patterns and item['pattern'] != 'insufficient evidence pattern':
            combo.append({
                'plant': item['plant'], 'pattern': item['pattern'],
                'composition': [c['name'] for c in item['promising_composition'][:2]],
                'reason': 'Distinct reported pattern that may complement another research candidate; requires literature and experimental validation.'
            })
            seen_patterns.add(item['pattern'])
        if len(combo) >= 4: break

    top_prediction = top[0] if top else None
    return {
        'query': payload.model_dump(),
        'engine': 'MedPlant AI v10 therapeutic candidate discovery',
        'model_status': 'AI-assisted research prediction prototype. The engine converts the query into biological concepts, compares those signals with every locally available plant profile, and ranks candidates using reported activity alignment, compound composition, target context, profile overlap and evidence completeness. It is not a separately trained clinical ML model.',
        'analysis_method': 'Hybrid AI-assisted semantic pattern recognition + weighted evidence scoring + compound prioritisation + target-context matching.',
        'prediction_summary': {
            'top_candidate': top_prediction['plant'] if top_prediction else None,
            'predicted_pattern': top_prediction['pattern'] if top_prediction else None,
            'pattern_strength': top_prediction['confidence_label'] if top_prediction else 'No supported pattern',
            'leading_composition': top_prediction['promising_composition'][0]['name'] if top_prediction and top_prediction['promising_composition'] else None,
            'matched_signals': top_prediction['matched_signals'] if top_prediction else [],
            'recommendation': top_prediction['prediction'] if top_prediction else 'Add more biological or molecular clues and enrich the local library.'
        },
        'medical_disclaimer': 'Results are research candidates and pattern hypotheses, not diagnoses, prescriptions, or proof that any plant or compound can prevent, treat, or cure a disease or virus.',
        'ranked_plants': top,
        'possible_combination_research': combo if len(combo) > 1 else [],
        'total_local_profiles_considered': len(grouped)
    }
