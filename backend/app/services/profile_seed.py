# Baseline project-profile metadata for the 100 starter plants. This is intentionally
# broad and source-aware; external NCBI/GBIF enrichment can replace/augment it.
FAMILIES={
'Abies':'Pinaceae','Abrus':'Fabaceae','Acacia':'Fabaceae','Aconitum':'Ranunculaceae','Acorus':'Acoraceae','Adhatoda':'Acanthaceae','Aegle':'Rutaceae','Albizia':'Fabaceae','Aloe':'Asphodelaceae','Alpinia':'Zingiberaceae','Alstonia':'Apocynaceae','Altingia':'Altingiaceae','Anacyclus':'Asteraceae','Andrographis':'Acanthaceae','Aquilaria':'Thymelaeaceae','Artemisia':'Asteraceae','Asparagus':'Asparagaceae','Atropa':'Solanaceae','Azadirachta':'Meliaceae','Bacopa':'Plantaginaceae','Berberis':'Berberidaceae','Bergenia':'Saxifragaceae','Boerhaavia':'Nyctaginaceae','Caesalpinia':'Fabaceae','Cassia':'Fabaceae','Catharanthus':'Apocynaceae','Celastrus':'Celastraceae','Centella':'Apiaceae','Chlorophytum':'Asparagaceae','Cinnamomum':'Lauraceae','Citrullus':'Cucurbitaceae','Clerodendrum':'Lamiaceae','Clitoria':'Fabaceae','Coleus':'Lamiaceae','Convolvulus':'Convolvulaceae','Cryptolepis':'Apocynaceae','Curcuma':'Zingiberaceae','Decalepis':'Apocynaceae','Digitalis':'Plantaginaceae','Dioscorea':'Dioscoreaceae','Eclipta':'Asteraceae','Embelia':'Primulaceae','Ephedra':'Ephedraceae','Garcinia':'Clusiaceae','Ginkgo':'Ginkgoaceae','Glycyrrhiza':'Fabaceae','Gymnema':'Apocynaceae','Hedychium':'Zingiberaceae','Hemidesmus':'Apocynaceae','Hibiscus':'Malvaceae','Holarrhena':'Apocynaceae','Homalomena':'Araceae','Hyoscyamus':'Solanaceae','Indigofera':'Fabaceae','Inula':'Asteraceae','Ipomoea':'Convolvulaceae','Jasminum':'Oleaceae','Juniperus':'Cupressaceae','Justicia':'Acanthaceae','Kaempferia':'Zingiberaceae','Lawsonia':'Lythraceae','Lepidium':'Brassicaceae','Moringa':'Moringaceae','Mucuna':'Fabaceae','Nardostachys':'Caprifoliaceae','Ocimum':'Lamiaceae','Paris':'Melanthiaceae','Picrorhiza':'Plantaginaceae','Piper':'Piperaceae','Plantago':'Plantaginaceae','Plumbago':'Plumbaginaceae','Podophyllum':'Berberidaceae','Pongamia':'Fabaceae','Rauvolfia':'Apocynaceae','Rheum':'Polygonaceae','Rosa':'Rosaceae','Rubia':'Rubiaceae','Santalum':'Santalaceae','Saussurea':'Asteraceae','Saraca':'Fabaceae','Sapindus':'Sapindaceae','Sida':'Malvaceae','Smilax':'Smilacaceae','Solanum':'Solanaceae','Strychnos':'Loganiaceae','Swertia':'Gentianaceae','Symplocos':'Symplocaceae','Terminalia':'Combretaceae','Withania':'Solanaceae'}
PARTS={'Abies':'Leaves / bark','Abrus':'Seeds / roots','Acacia':'Bark / heartwood','Aconitum':'Roots','Acorus':'Rhizome','Adhatoda':'Leaves','Aegle':'Leaves / fruit','Albizia':'Bark / leaves','Aloe':'Leaf gel','Alpinia':'Rhizome','Alstonia':'Bark / leaves','Altingia':'Resin / bark','Anacyclus':'Root','Andrographis':'Leaves / aerial parts','Aquilaria':'Heartwood / resin','Artemisia':'Aerial parts','Asparagus':'Root','Atropa':'Leaves / roots','Azadirachta':'Leaves / seed / bark','Bacopa':'Whole plant','Berberis':'Root / stem bark','Bergenia':'Rhizome','Boerhaavia':'Root / whole plant','Caesalpinia':'Heartwood','Cassia':'Leaves / pods','Catharanthus':'Leaves / aerial parts','Celastrus':'Seeds / oil','Centella':'Whole plant','Chlorophytum':'Roots','Cinnamomum':'Bark / leaves','Citrullus':'Seeds / fruit','Clerodendrum':'Leaves / roots','Clitoria':'Roots / flowers','Coleus':'Roots','Convolvulus':'Whole plant','Cryptolepis':'Root','Curcuma':'Rhizome','Decalepis':'Root','Digitalis':'Leaves','Dioscorea':'Tuber','Eclipta':'Whole plant','Embelia':'Fruit','Ephedra':'Aerial stems','Garcinia':'Fruit rind','Ginkgo':'Leaves','Glycyrrhiza':'Root','Gymnema':'Leaves','Hedychium':'Rhizome','Hemidesmus':'Root','Hibiscus':'Flowers / leaves','Holarrhena':'Bark / seeds','Homalomena':'Rhizome','Hyoscyamus':'Leaves / seeds','Indigofera':'Leaves','Inula':'Root','Ipomoea':'Root / seeds','Jasminum':'Flowers / leaves','Juniperus':'Berries / leaves','Justicia':'Leaves','Kaempferia':'Rhizome','Lawsonia':'Leaves','Lepidium':'Seeds','Moringa':'Leaves / seeds','Mucuna':'Seeds','Nardostachys':'Rhizome / root','Ocimum':'Leaves / aerial parts','Paris':'Rhizome','Picrorhiza':'Rhizome','Piper':'Fruit','Plantago':'Seeds / husk','Plumbago':'Root','Podophyllum':'Rhizome / root','Pongamia':'Seeds / oil','Rauvolfia':'Root','Rheum':'Rhizome / root','Rosa':'Flowers','Rubia':'Root','Santalum':'Heartwood','Saussurea':'Root','Saraca':'Bark / flowers','Sapindus':'Fruit pericarp','Sida':'Roots / aerial parts','Smilax':'Root / rhizome','Solanum':'Leaves / fruits / roots','Strychnos':'Seeds / bark','Swertia':'Whole plant','Symplocos':'Bark','Terminalia':'Fruit / bark','Withania':'Root / leaves'}

def profile_for(scientific, common):
    genus=scientific.split()[0]
    family=FAMILIES.get(genus)
    part=PARTS.get(genus)
    special=FOUR_POSTER_PROFILES.get(scientific,{})
    return {
      'family':special.get('family') or family,
      'plant_part_used':special.get('plant_part_used') or part,
      'genomic_background':special.get('genomic_background'),
      'phytochemical_information':special.get('phytochemical_information'),
      'reported_biological_activities':special.get('reported_biological_activities'),
      'description':f'{common} ({scientific}) is a medicinal-plant record in the MedPlant AI starter library. The profile combines plant identity, chemical context and genomic context for computational analysis.',
      'traditional_relevance':f'Reported in traditional medicinal use; this project records the plant for phytochemical, therapeutic-category and genomic exploration. Typical project-listed material: {part or "plant material"}. Specific therapeutic claims require source validation.'
    }


FOUR_POSTER_PROFILES={
    'Azadirachta indica': {
        'family':'Meliaceae', 'plant_part_used':'Leaves / seeds / bark',
        'genomic_background':'Neem is the species Azadirachta indica (Meliaceae). The profile links plant identity to NCBI taxonomy and GenBank/nucleotide records so genomic context can be connected to phytochemical analysis. Genomic records shown in the app are source-linked database records, not a claim of a complete reference genome.',
        'phytochemical_information':'Poster-highlighted phytochemical: Azadirachtin. The compound profile includes chemical structure, formula, molecular weight, XLogP/logP and additional computed molecular properties.',
        'reported_biological_activities':'Azadirachtin is reported primarily for insecticidal and antifeedant activity. These are reported biological associations, not a newly discovered activity in this project.',
    },
    'Ocimum tenuiflorum': {
        'family':'Lamiaceae', 'plant_part_used':'Leaves / aerial parts',
        'genomic_background':'Tulsi (Ocimum tenuiflorum) is a Lamiaceae medicinal plant with published genomic resources. The profile connects species identity with NCBI taxonomy and GenBank/nucleotide records for genomic exploration.',
        'phytochemical_information':'Poster-highlighted phytochemical: Ursolic Acid. The compound profile includes chemical structure, formula, molecular weight, XLogP/logP and additional computed molecular properties.',
        'reported_biological_activities':'Ursolic Acid is reported in the project literature context with antimicrobial and antioxidant activities. These are reported associations and require literature/experimental validation.',
    },
    'Curcuma longa': {
        'family':'Zingiberaceae', 'plant_part_used':'Rhizome',
        'genomic_background':'Turmeric (Curcuma longa) is a Zingiberaceae plant. Its profile connects species identity with NCBI taxonomy and available nucleotide/GenBank records for genomic context.',
        'phytochemical_information':'Poster-highlighted phytochemical: Curcumin. The compound profile includes chemical structure, formula, molecular weight, XLogP/logP and additional computed molecular properties.',
        'reported_biological_activities':'Curcumin is reported with anti-inflammatory and antioxidant activities in the project context. These are reported biological associations, not a new discovery by the application.',
    },
    'Withania somnifera': {
        'family':'Solanaceae', 'plant_part_used':'Root / leaves',
        'genomic_background':'Ashwagandha (Withania somnifera) is a Solanaceae medicinal plant. The profile connects species identity with NCBI taxonomy and available nucleotide/GenBank records for genomic context.',
        'phytochemical_information':'Poster-highlighted phytochemical: Withaferin A. The compound profile includes chemical structure, formula, molecular weight, XLogP/logP and additional computed molecular properties.',
        'reported_biological_activities':'Withaferin A is reported with anti-inflammatory and antioxidant activities in the project context. These are reported associations and require literature/experimental validation.',
    },
}

def specialized_profile(scientific):
    return FOUR_POSTER_PROFILES.get(scientific, {})
