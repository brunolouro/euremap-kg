#!/usr/bin/env python3
"""Generate the EUREMAP instance graph (ABox) from the parsed catalogue snapshot."""
import json, re, csv
from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import RDF, RDFS, SKOS, DCTERMS as DCT, XSD, OWL, FOAF, DCAT, PROV
from rdflib.collection import Collection

EUR = Namespace("https://w3id.org/euremap/ontology/")
RES = Namespace("https://w3id.org/euremap/resource/")
ORG = Namespace("http://www.w3.org/ns/org#")
SCHEMA = Namespace("https://schema.org/")
OBO = Namespace("http://purl.obolibrary.org/obo/")
EDAM = Namespace("http://edamontology.org/")
WD = Namespace("http://www.wikidata.org/entity/")
EUC = Namespace("http://publications.europa.eu/resource/authority/country/")
BIOTOOLS = Namespace("https://bio.tools/")

S = json.load(open("source/catalogue-snapshot-2026-11-19.json"))
g = Graph()
for p, ns in [("eur", EUR), ("res", RES), ("org", ORG), ("schema", SCHEMA), ("skos", SKOS),
              ("dct", DCT), ("dcat", DCAT), ("prov", PROV), ("foaf", FOAF), ("obo", OBO),
              ("edam", EDAM), ("wd", WD), ("euc", EUC), ("biotools", BIOTOOLS), ("owl", OWL), ("xsd", XSD)]:
    g.bind(p, ns)

def L(s, lang="en"): return Literal(s, lang=lang)
SNAP = "2026-11-19"

# --------------------------------------------------------------------------- catalogue / provenance
CAT = RES["catalogue-euremap"]
g.add((CAT, RDF.type, EUR.ServiceCatalogue))
g.add((CAT, DCT.title, L("EUREMAP – Pipeline of Marine Bioprospecting Services Catalogue")))
g.add((CAT, FOAF.homepage, URIRef("https://services.euremap.eu/")))
g.add((CAT, DCT.publisher, RES["project-euremap"]))
g.add((RES["project-euremap"], RDF.type, FOAF.Project))
g.add((RES["project-euremap"], RDFS.label, L("EUREMAP")))
g.add((RES["project-euremap"], FOAF.homepage, URIRef("https://euremap.eu/")))
KG = RES["dataset-euremap-kg"]
g.add((KG, RDF.type, DCAT.Dataset)); g.add((KG, RDF.type, PROV.Entity))
g.add((KG, DCT.title, L("EUREMAP service knowledge graph (instance data)")))
g.add((KG, DCT.conformsTo, URIRef("https://w3id.org/euremap/ontology")))
g.add((KG, PROV.wasDerivedFrom, CAT))
g.add((KG, DCT.issued, Literal(SNAP, datatype=XSD.date)))
g.add((KG, DCT.description, L("Generated from the public catalogue listing and the 71 service detail pages retrieved on 2026-11-19. Capability tags are assigned by controlled keyword matching; national nodes are derived from service affiliations. Personal contact e-mails are intentionally not included.")))

# --------------------------------------------------------------------------- countries
COUNTRIES = {  # name: (alpha2, alpha3, wikidata)
    "Norway": ("NO", "NOR", "Q20"), "Portugal": ("PT", "PRT", "Q45"), "Italy": ("IT", "ITA", "Q38"),
    "Germany": ("DE", "DEU", "Q183"), "France": ("FR", "FRA", "Q142"), "Spain": ("ES", "ESP", "Q29"),
    "Israel": ("IL", "ISR", "Q801"), "Belgium": ("BE", "BEL", "Q31"), "United Kingdom": ("GB", "GBR", "Q145")}
def country(name):
    a2, a3, q = COUNTRIES[name]
    c = RES[f"country-{a2}"]
    g.add((c, RDF.type, EUR.Country)); g.add((c, SKOS.prefLabel, L(name)))
    g.add((c, EUR.iso3166Alpha2, Literal(a2)))
    g.add((c, SKOS.exactMatch, EUC[a3])); g.add((c, SKOS.exactMatch, WD[q]))
    return c

# --------------------------------------------------------------------------- research infrastructures
RIS = {"EMBRC": ("ri-embrc", "European Marine Biological Resource Centre", "0038zss60", "https://www.embrc.eu/"),
       "EU-OPENSCREEN": ("ri-eu-openscreen", "EU-OPENSCREEN", "055zp1089", "https://www.eu-openscreen.eu/"),
       "EMBL": ("ri-embl", "European Molecular Biology Laboratory", "03mstc592", "https://www.embl.org/")}
for k, (slug, name, ror, url) in RIS.items():
    r = RES[slug]
    g.add((r, RDF.type, EUR.ResearchInfrastructure)); g.add((r, SKOS.prefLabel, L(name)))
    g.add((r, SKOS.altLabel, L(k))); g.add((r, EUR.rorId, Literal(ror)))
    g.add((r, OWL.sameAs, URIRef("https://ror.org/" + ror))); g.add((r, FOAF.homepage, URIRef(url)))

# --------------------------------------------------------------------------- institutions
# catalogue label -> (slug, preferred name, acronym, ROR, parent)
INST = {
 "SINTEF": ("org-sintef", "SINTEF", "SINTEF", "01f677e56", None),
 "Centro de Ciências do Mar do Algarve": ("org-ccmar", "Centro de Ciências do Mar do Algarve", "CCMAR", "00me37y22", None),
 "Helmholtz Centre for Infection Research": ("org-hzi", "Helmholtz Centre for Infection Research", "HZI", "03d0p2685", None),
 "Sorbonne Université": ("org-su", "Sorbonne Université", "SU", "02en5vm52", None),
 "MEDINA": ("org-medina", "Fundación MEDINA", "MEDINA", "042dh5y83", None),
 "CNR": ("org-cnr", "Consiglio Nazionale delle Ricerche", "CNR", "04zaypm56", None),
 "UiT The Artic University of Norway": ("org-uit", "UiT The Arctic University of Norway", "UiT", "00wge5k78", None),
 "Stazione Zoologica Anton Dohrn Napoli": ("org-szn", "Stazione Zoologica Anton Dohrn", "SZN", "03v5jj203", None),
 "Tel Aviv University": ("org-tau", "Tel Aviv University", "TAU", "04mhzgx49", None),
 "Ghent University": ("org-ugent", "Ghent University", "UGent", "00cv9y106", None),
 "EMBL's European Bioinformatics Institute": ("org-embl-ebi", "EMBL's European Bioinformatics Institute", "EMBL-EBI", "02catss52", "ri-embl"),
}
def institution(label, cname):
    slug, name, acr, ror, parent = INST[label]
    o = RES[slug]
    g.add((o, RDF.type, EUR.Institution)); g.add((o, SKOS.prefLabel, L(name)))
    g.add((o, SKOS.altLabel, L(acr)))
    if label != name: g.add((o, EUR.catalogueLabel, L(label)))
    g.add((o, EUR.rorId, Literal(ror))); g.add((o, OWL.sameAs, URIRef("https://ror.org/" + ror)))
    g.add((o, EUR.locatedInCountry, country(cname)))
    if parent: g.add((o, ORG.subOrganizationOf, RES[parent]))
    return o

# organisational units (catalogue label -> slug, preferred label, optional ROR)
UNIT_FIX = {
 "Bio2Mar, Sorbonne Université, Observatoire Océanologique de Banyuls": "Bio2Mar platform, Sorbonne Université, Observatoire Océanologique de Banyuls",
 "Ecostustainable Marine Biotechnology Department": "Ecosustainable Marine Biotechnology Department",
 "Marbio , Faculty of Biosciences, fisheries & economics": "Marbio, Faculty of Biosciences, Fisheries and Economics",
 "Laboratory of Pharmaceutical Microbiology\xa0(LPM)": "Laboratory of Pharmaceutical Microbiology (LPM)",
}
UNIT_ROR = {"CNR-Institute of Biomolecular Chemistry (ICB)": "03wyf0g15"}
def slugify(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]
def unit(label, inst_node, inst_slug):
    pref = UNIT_FIX.get(label, label)
    u = RES[f"unit-{inst_slug[4:]}-{slugify(pref)}"]
    g.add((u, RDF.type, EUR.OrganisationalUnit)); g.add((u, SKOS.prefLabel, L(pref)))
    if pref != label: g.add((u, EUR.catalogueLabel, L(label)))
    g.add((u, ORG.unitOf, inst_node)); g.add((inst_node, ORG.hasUnit, u))
    if pref in UNIT_ROR or label in UNIT_ROR:
        ror = UNIT_ROR.get(pref) or UNIT_ROR[label]
        g.add((u, EUR.rorId, Literal(ror))); g.add((u, OWL.sameAs, URIRef("https://ror.org/" + ror)))
    return u

# --------------------------------------------------------------------------- phases & steps
PHASES = {"phase-genomic": ("Genomic & biological resources", 1),
          "phase-chemistry": ("Chemistry", 2),
          "phase-bioactivity": ("Bioactivity & safety", 3)}
for slug, (lab, n) in PHASES.items():
    p = RES[slug]; g.add((p, RDF.type, EUR.PipelinePhase)); g.add((p, SKOS.prefLabel, L(lab)))
    g.add((p, SKOS.inScheme, RES["scheme-phases"])); g.add((p, SKOS.topConceptOf, RES["scheme-phases"]))
    g.add((p, SKOS.notation, Literal(str(n))))

# catalogue short label -> (slug, full label, order, phase, inputs, outputs, definition)
STEPS = {
 "Genomics": ("step-genomics", "Genomics", 1, "phase-genomic",
    ["mat-environmental-sample", "mat-raw-reads"], ["mat-metagenome-assembly", "mat-mag", "mat-bgc-prediction", "mat-taxonomic-functional-profile"],
    "Sequencing, assembly, binning and annotation of (meta)genomes, including mining for biosynthetic gene clusters."),
 "Biomass production": ("step-biomass-production", "Biomass production", 2, "phase-genomic",
    ["mat-microbial-strain"], ["mat-biomass", "mat-culture-broth"],
    "Cultivation and scale-up of microorganisms to produce biomass and conditioned culture media."),
 "Chemical Extraction": ("step-chemical-extraction", "Chemical extraction", 3, "phase-chemistry",
    ["mat-biomass", "mat-culture-broth"], ["mat-crude-extract"],
    "Extraction of metabolites from biomass, cell pellets or culture media to yield crude extracts."),
 "Bioassays & bioprofiling": ("step-bioassays", "Bioassays & bioprofiling", 4, "phase-bioactivity",
    ["mat-crude-extract", "mat-fraction", "mat-pure-compound", "mat-synthetic-analogue"], ["mat-bioactivity-data"],
    "Screening and profiling of extracts, fractions and compounds for biological activities and mode of action."),
 "Safety & toxicity": ("step-safety-toxicity", "Safety and toxicity profiling", 5, "phase-bioactivity",
    ["mat-fraction", "mat-pure-compound", "mat-synthetic-analogue"], ["mat-safety-data"],
    "Dose-response human-safety, ecotoxicity and in vivo safety assessment."),
 "Chemical profiling": ("step-chemical-profiling", "Chemical profiling", 6, "phase-chemistry",
    ["mat-crude-extract", "mat-fraction"], ["mat-chemical-profile-data"],
    "Untargeted/targeted chemical characterisation (LC-MS, NMR etc.) supporting dereplication and prioritisation."),
 "Chromatography": ("step-chromatography", "Chromatography & purification", 7, "phase-chemistry",
    ["mat-crude-extract", "mat-fraction"], ["mat-fraction", "mat-pure-compound"],
    "Fractionation and purification of extracts to obtain fractions and pure compounds."),
 "Structure elucidation": ("step-structure-elucidation", "Structure elucidation", 8, "phase-chemistry",
    ["mat-pure-compound"], ["mat-chemical-structure"],
    "Determination of planar structure and stereochemistry of purified compounds."),
 "Synthesis": ("step-synthesis", "Synthesis & semi-synthesis", 9, "phase-chemistry",
    ["mat-chemical-structure", "mat-pure-compound"], ["mat-synthetic-analogue", "mat-in-silico-model"],
    "Total synthesis, semi-synthesis, analogue design and computational chemistry."),
}
MATERIALS = {  # slug: (label, physical?)
 "mat-environmental-sample": ("Environmental or biological sample", True),
 "mat-raw-reads": ("Raw sequencing reads", False),
 "mat-metagenome-assembly": ("Metagenome or genome assembly", False),
 "mat-mag": ("Metagenome-assembled genome (MAG)", False),
 "mat-bgc-prediction": ("Biosynthetic gene cluster prediction", False),
 "mat-taxonomic-functional-profile": ("Taxonomic and functional profile", False),
 "mat-microbial-strain": ("Microbial strain or culture", True),
 "mat-biomass": ("Microbial biomass / cell pellet", True),
 "mat-culture-broth": ("Culture medium (broth)", True),
 "mat-crude-extract": ("Crude extract", True),
 "mat-fraction": ("Chromatographic fraction", True),
 "mat-pure-compound": ("Purified compound", True),
 "mat-synthetic-analogue": ("Synthetic or semi-synthetic analogue", True),
 "mat-chemical-profile-data": ("Chemical profile data (MS/NMR)", False),
 "mat-chemical-structure": ("Elucidated chemical structure", False),
 "mat-bioactivity-data": ("Bioactivity data", False),
 "mat-safety-data": ("Safety and toxicity data", False),
 "mat-in-silico-model": ("In silico model (docking/QSAR)", False),
}
for slug, (lab, phys) in MATERIALS.items():
    m = RES[slug]; g.add((m, RDF.type, EUR.PhysicalMaterialType if phys else EUR.DigitalDataType))
    g.add((m, RDF.type, EUR.MaterialOrDataType)); g.add((m, SKOS.prefLabel, L(lab))); g.add((m, SKOS.inScheme, RES["scheme-materials"]))
g.add((RES["mat-raw-reads"], SKOS.closeMatch, EDAM.data_3494))  # DNA sequence (raw) — closeMatch only
g.add((RES["mat-metagenome-assembly"], SKOS.closeMatch, EDAM.data_0925))  # Sequence assembly (verified via OLS)

step_nodes = {}
ordered = sorted(STEPS.values(), key=lambda x: x[2])
for slug, lab, n, ph, ins, outs, defi in ordered:
    s = RES[slug]; step_nodes[slug] = s
    g.add((s, RDF.type, EUR.PipelineStep)); g.add((s, SKOS.prefLabel, L(lab)))
    g.add((s, SKOS.definition, L(defi))); g.add((s, EUR.stepOrder, Literal(n, datatype=XSD.integer)))
    g.add((s, SKOS.notation, Literal(f"{n:02d}"))); g.add((s, SKOS.inScheme, RES["scheme-pipeline"]))
    g.add((s, EUR.inPhase, RES[ph]))
    for i in ins: g.add((s, EUR.typicalInput, RES[i]))
    for o in outs: g.add((s, EUR.typicalOutput, RES[o]))
for a, b in zip(ordered, ordered[1:]):
    g.add((RES[a[0]], EUR.nextStep, RES[b[0]]))
for k, v in STEPS.items(): g.add((RES[v[0]], EUR.catalogueLabel, L(k)))
# cross-cutting FAIR data step from the euremap.eu pipeline page (no catalogue services yet)
fair = RES["step-fair-data"]
g.add((fair, RDF.type, EUR.PipelineStep)); g.add((fair, SKOS.prefLabel, L("FAIR data")))
g.add((fair, SKOS.definition, L("Cross-cutting data management: access procedures, repositories, standards and data-management policies. Listed on the EUREMAP service-pipeline page; no catalogue services are attached to it in the 2026-11-19 snapshot.")))
g.add((fair, SKOS.inScheme, RES["scheme-pipeline"])); g.add((fair, RDFS.seeAlso, URIRef("https://euremap.eu/service-pipeline/")))

# --------------------------------------------------------------------------- access, fees, quantity kinds
ACCESS = {"Physical": ("access-physical", "Physical access", "The user (or user's samples and staff) works on-site at the provider's facility."),
          "Remote": ("access-remote", "Remote access", "The user sends samples or requests; the provider performs the service and returns results."),
          "Virtual": ("access-virtual", "Virtual access", "Free, open, online access to data resources or analysis services without selection of individual users.")}
for k, (slug, lab, d) in ACCESS.items():
    a = RES[slug]; g.add((a, RDF.type, EUR.AccessMode)); g.add((a, SKOS.prefLabel, L(lab)))
    g.add((a, SKOS.definition, L(d))); g.add((a, SKOS.inScheme, RES["scheme-access"]))
FEES = {"fee-free": "Free of charge", "fee-for-service": "Fee-for-service", "fee-on-request": "Cost on request (depends on material)"}
for slug, lab in FEES.items():
    f = RES[slug]; g.add((f, RDF.type, EUR.FeeModel)); g.add((f, SKOS.prefLabel, L(lab))); g.add((f, SKOS.inScheme, RES["scheme-fees"]))
QK = {"qk-culture-volume": "Culture / processing volume", "qk-extraction-mass": "Processing mass",
      "qk-sample-requirement": "Sample amount required per assay", "qk-purification-yield": "Purified compound yield",
      "qk-input-extract-mass": "Input extract mass", "qk-nmr-field": "NMR field strength"}
for slug, lab in QK.items():
    q = RES[slug]; g.add((q, RDF.type, EUR.QuantityKind)); g.add((q, SKOS.prefLabel, L(lab))); g.add((q, SKOS.inScheme, RES["scheme-quantities"]))

ENA = RES["repo-ena"]
g.add((ENA, RDF.type, EUR.Repository)); g.add((ENA, SKOS.prefLabel, L("European Nucleotide Archive (ENA)")))
g.add((ENA, FOAF.homepage, URIRef("https://www.ebi.ac.uk/ena/browser/"))); g.add((ENA, DCT.publisher, RES["org-embl-ebi"]))

# --------------------------------------------------------------------------- software
SOFT = {"antiSMASH": ("sw-antismash", "antismash", r"antismash"), "BiG-SCAPE": ("sw-big-scape", "big-scape", r"big-scape"),
        "SanntiS": ("sw-sanntis", "sanntis", r"sanntis"), "Nextflow": ("sw-nextflow", "nextflow", r"nextflow"),
        "MGnify": ("sw-mgnify", "mgnify", r"mgnify|ebi\.ac\.uk/metagenomics|mgnify-bgcs")}
for lab, (slug, bt, _) in SOFT.items():
    t = RES[slug]; g.add((t, RDF.type, EUR.SoftwareTool)); g.add((t, RDFS.label, L(lab)))
    g.add((t, SKOS.exactMatch, BIOTOOLS[bt]))  # bio.tools IDs verified (HTTP 200) on 2026-11-19

# --------------------------------------------------------------------------- capability taxonomy
# (slug, label, broader, steps-allowed, regex, [(matchType, IRI)])
GEN = ["Genomics"]; BIO = ["Biomass production"]; EXT = ["Chemical Extraction"]
ASSAY = ["Bioassays & bioprofiling", "Safety & toxicity"]
ANAL = ["Chemical profiling", "Structure elucidation", "Chromatography"]
CHR = ["Chromatography"]; STR = ["Structure elucidation"]; SYN = ["Synthesis"]
CAPS = [
 # top concepts
 ("cap-genomic-analysis", "Genomic analysis", None, [], None, [("close", EDAM.operation_3918)]),
 ("cap-cultivation", "Microbial cultivation", None, [], None, []),
 ("cap-extraction", "Chemical extraction", None, [], None, [("broad", OBO.CHMO_0001598)]),
 ("cap-bioassay", "Bioactivity assay", None, [], None, []),
 ("cap-safety-assessment", "Safety and toxicity assessment", None, [], None, []),
 ("cap-analytical-technique", "Analytical technique", None, [], None, []),
 ("cap-separation", "Separation and purification", None, [], None, []),
 ("cap-stereochemistry", "Stereochemical analysis", None, [], None, []),
 ("cap-synthesis", "Chemical synthesis", None, [], None, []),
 ("cap-computational-chemistry", "Computational chemistry", None, [], None, []),
 # genomics
 ("cap-illumina-sequencing", "Illumina short-read sequencing", "cap-genomic-analysis", GEN, r"illumina|short-read", [("broad", EDAM.topic_3168)]),
 ("cap-nanopore-sequencing", "Oxford Nanopore long-read sequencing", "cap-genomic-analysis", GEN, r"\bont\b|nanopore|long-read", [("broad", EDAM.topic_3168)]),
 ("cap-metagenome-assembly", "(Meta)genome assembly", "cap-genomic-analysis", GEN, r"assembl", [("close", EDAM.operation_0310), ("related", EDAM.topic_3174)]),
 ("cap-mag-binning", "MAG recovery and quality assessment", "cap-genomic-analysis", GEN, r"\bmags?\b", []),
 ("cap-taxonomic-classification", "Taxonomic classification", "cap-genomic-analysis", GEN, r"taxonom", [("exact", EDAM.operation_3460)]),
 ("cap-gene-prediction", "Gene prediction", "cap-genomic-analysis", GEN, r"gene prediction", [("exact", EDAM.operation_2454)]),
 ("cap-functional-annotation", "Functional annotation", "cap-genomic-analysis", GEN, r"functional (assignment|annotation|and taxonomic annotation)|annotation", [("close", EDAM.operation_3672)]),
 ("cap-bgc-mining", "Biosynthetic gene cluster mining", "cap-genomic-analysis", GEN, r"\bbgcs?\b|biosynthetic gene cluster", [("related", EDAM.operation_3803)]),
 ("cap-workflow-automation", "Automated workflow execution", "cap-genomic-analysis", GEN, r"nextflow|automated (workflow|metagenomic)", [("close", EDAM.topic_0769)]),
 # cultivation
 ("cap-bacterial-cultivation", "Bacterial cultivation", "cap-cultivation", BIO, r"bacteri|microbial", []),
 ("cap-fungal-cultivation", "Fungal cultivation", "cap-cultivation", BIO, r"fung", []),
 ("cap-anaerobic-cultivation", "Anaerobic cultivation", "cap-cultivation", BIO, r"anaerob", []),
 ("cap-bioreactor-cultivation", "Bioreactor cultivation and scale-up", "cap-cultivation", BIO, r"bioreactor|scale-up", []),
 ("cap-photobioreactor", "Photobioreactor cultivation", "cap-bioreactor-cultivation", BIO, r"photobioreactor", []),
 # extraction
 ("cap-culture-medium-extraction", "Culture-medium extraction", "cap-extraction", EXT, r"culture media", []),
 ("cap-biomass-extraction", "Biomass extraction", "cap-extraction", EXT, r"extraction of biomass|biomass and culture", []),
 ("cap-cell-pellet-extraction", "Cell-pellet extraction", "cap-extraction", EXT, r"cell pellet", []),
 # bioassays
 ("cap-antimicrobial-assay", "Antimicrobial assay", "cap-bioassay", ASSAY, r"antimicrobial|mic70", []),
 ("cap-antibacterial-assay", "Antibacterial assay", "cap-antimicrobial-assay", ASSAY, r"antibacterial", []),
 ("cap-antifungal-assay", "Antifungal assay", "cap-antimicrobial-assay", ASSAY, r"antifungal", []),
 ("cap-antibiofilm-assay", "Antibiofilm assay", "cap-antimicrobial-assay", ASSAY, r"antibiofilm|biofilm", []),
 ("cap-antiviral-assay", "Antiviral assay", "cap-bioassay", ASSAY, r"antiviral", []),
 ("cap-anticancer-assay", "Anticancer assay", "cap-bioassay", ASSAY, r"anticancer", []),
 ("cap-immunomodulatory-assay", "Immunomodulatory assay", "cap-bioassay", ASSAY, r"immunomodul", []),
 ("cap-antioxidant-assay", "Antioxidant assay", "cap-bioassay", ASSAY, r"antioxidant", []),
 ("cap-antifouling-assay", "Antifouling assay", "cap-bioassay", ASSAY, r"antifouling", []),
 ("cap-agri-crop-assay", "Agriculture and crop-protection assay", "cap-bioassay", ASSAY, r"agricultur|\bcrop", []),
 ("cap-enzyme-assay", "Enzyme activity / inhibition assay", "cap-bioassay", ASSAY, r"enzym|kinase|lipase|chitinase|collag|proteinase|cellulase|amylase", []),
 ("cap-kinase-assay", "Kinase inhibition assay", "cap-enzyme-assay", ASSAY, r"kinase", []),
 ("cap-hydrolase-assay", "Hydrolytic enzyme activity screening", "cap-enzyme-assay", ASSAY, r"lipase|chitinase|collag|proteinase|cellulase|amylase", []),
 ("cap-ppi-assay", "Protein–protein interaction assay", "cap-bioassay", ASSAY, r"protein-protein interaction", [("related", EDAM.topic_0128)]),
 ("cap-admet", "ADMET profiling", "cap-bioassay", ASSAY, r"admet", []),
 ("cap-receptor-signalling-assay", "Receptor-activation / cell-signalling assay", "cap-bioassay", ASSAY, r"receptor|cell signalling", []),
 ("cap-impedance-cell-assay", "Impedance-based cell assay (ECIS/TEER)", "cap-bioassay", ASSAY, r"ecis|teer|impedance", []),
 ("cap-cell-migration-assay", "Cell migration and wound-healing assay", "cap-bioassay", ASSAY, r"migration|wound healing", []),
 ("cap-cell-viability-assay", "Cell viability / metabolic activity assay", "cap-bioassay", ASSAY, r"\bmtt\b|viability|metabolic activity|proliferation", []),
 ("cap-target-identification", "Target identification and mode of action (chemoproteomics)", "cap-bioassay", ASSAY, r"chemoproteom|target fishing|mode-of-action|mode of action", []),
 ("cap-dose-response", "Dose-response assay", "cap-bioassay", ASSAY, r"dose-response|mic70", []),
 # safety
 ("cap-human-cell-toxicity", "Human cell-line toxicity", "cap-safety-assessment", ASSAY, r"human cell line|human safety|toxicity", []),
 ("cap-ecotoxicity", "Ecotoxicity", "cap-safety-assessment", ASSAY, r"ecotox|non-vertebrate", []),
 ("cap-in-vivo-safety", "In vivo safety (mouse)", "cap-safety-assessment", ASSAY, r"in vivo|mice", []),
 ("cap-biodistribution", "Compound biodistribution / exposure", "cap-safety-assessment", ASSAY, r"blood and selected organs|compound concentration", []),
 ("cap-toxicotranscriptomics", "Transcriptomics for off-target toxicity", "cap-safety-assessment", ASSAY, r"transcriptom", [("related", EDAM.topic_3308)]),
 # analytical
 ("cap-mass-spectrometry", "Mass spectrometry", "cap-analytical-technique", ANAL, r"\bms\b|-ms|ms2|msn|maldi|qtof|qqq|ft-icr", [("exact", OBO.CHMO_0000470)]),
 ("cap-lc-ms", "Liquid chromatography–mass spectrometry", "cap-mass-spectrometry", ANAL, r"lc-ms|lc-hrms|lc/hrms|hplc-hr-ms|uhplc-hr-ms|uhplc-ms|uhplc-ims|uhplc-hrms", [("exact", OBO.CHMO_0000524)]),
 ("cap-hrms", "High-resolution mass spectrometry", "cap-mass-spectrometry", ANAL, r"hr-ms|hrms|high-resolution|ft-icr|qtof", [("exact", OBO.CHMO_0000498)]),
 ("cap-tandem-ms", "Tandem mass spectrometry (MS/MS, MSn)", "cap-mass-spectrometry", ANAL, r"ms2|ms/ms|msn|ms-ms", [("exact", OBO.CHMO_0000575)]),
 ("cap-gc-ms", "Gas chromatography–mass spectrometry", "cap-mass-spectrometry", ANAL, r"gc-ms|gc-hr-ms", [("exact", OBO.CHMO_0000497)]),
 ("cap-maldi-ms", "MALDI mass spectrometry", "cap-mass-spectrometry", ANAL, r"maldi", [("close", OBO.CHMO_0000519)]),
 ("cap-esi-ms", "Electrospray ionisation MS", "cap-mass-spectrometry", ANAL, r"\besi\b|maldi-esi|electrospray", [("exact", OBO.CHMO_0000482)]),
 ("cap-ft-icr-ms", "FT-ICR mass spectrometry", "cap-hrms", ANAL, r"ft-icr", [("exact", OBO.CHMO_0000502)]),
 ("cap-qtof-ms", "Q-TOF mass spectrometry", "cap-hrms", ANAL, r"qtof", [("exact", OBO.CHMO_0002719)]),
 ("cap-qqq-ms", "Triple-quadrupole mass spectrometry", "cap-mass-spectrometry", ANAL, r"qqq|triple quadrupole", [("related", OBO.CHMO_0002021)]),
 ("cap-rapidfire-ms", "RapidFire high-throughput MS", "cap-mass-spectrometry", ANAL, r"rapidfire", []),
 ("cap-ion-mobility", "Ion mobility spectrometry", "cap-analytical-technique", ANAL, r"\bims\b|ion mobility", [("close", OBO.CHMO_0000430)]),
 ("cap-nmr", "NMR spectroscopy", "cap-analytical-technique", ANAL, r"nmr", [("exact", OBO.CHMO_0000591)]),
 ("cap-nmr-cryoprobe", "Cryoprobe NMR", "cap-nmr", ANAL, r"cryoprobe", []),
 ("cap-nmr-2d", "1D/2D NMR interpretation", "cap-nmr", ANAL, r"2d nmr|1d and 2d", []),
 ("cap-hplc", "HPLC", "cap-analytical-technique", ANAL, r"hplc", [("exact", OBO.CHMO_0001009)]),
 ("cap-uhplc", "UHPLC", "cap-hplc", ANAL, r"uhplc", [("exact", OBO.CHMO_0000795)]),
 ("cap-gc", "Gas chromatography", "cap-analytical-technique", ANAL, r"\bgc\b|gc-", [("exact", OBO.CHMO_0001002)]),
 ("cap-dad-uv", "UV/DAD detection", "cap-analytical-technique", ANAL, r"\buv\b|uv/vis|uv-based|\bdad\b|-dad", [("close", OBO.CHMO_0000292)]),
 ("cap-ir", "Infrared spectroscopy", "cap-analytical-technique", ANAL, r"\bir\b|infrared", [("close", OBO.CHMO_0000630)]),
 ("cap-cd", "Circular dichroism", "cap-analytical-technique", ANAL, r"\bcd\b|circular dichroism", [("exact", OBO.CHMO_0000323)]),
 ("cap-polarimetry", "Polarimetry / optical rotation", "cap-analytical-technique", ANAL, r"polarimetry|optical rotation", [("exact", OBO.CHMO_0000779)]),
 ("cap-feature-annotation", "Metabolomics feature extraction and annotation", "cap-analytical-technique", ANAL, r"feature extraction|statistical analysis|annotation", []),
 # separation
 ("cap-fractionation", "Fractionation", "cap-separation", CHR, r"fractionat", [("exact", OBO.CHMO_0001625)]),
 ("cap-purification", "Compound purification", "cap-separation", CHR, r"purif|pure compound", []),
 ("cap-column-chromatography", "Column chromatography", "cap-separation", CHR, r"column chromatography", [("exact", OBO.CHMO_0001001)]),
 ("cap-flash-chromatography", "Flash chromatography", "cap-separation", CHR, r"flash", [("exact", OBO.CHMO_0002582)]),
 ("cap-preparative-hplc", "(Semi-)preparative HPLC", "cap-separation", CHR, r"preparative", [("broad", OBO.CHMO_0001009)]),
 ("cap-ms-triggered-purification", "MS-/UV-triggered automated purification", "cap-separation", CHR, r"triggered by ms|automation triggered", []),
 ("cap-remote-process-control", "Remotely controlled purification", "cap-separation", CHR, r"remote process control|controlled remotely|remote operation", []),
 # stereochemistry
 ("cap-chiral-analysis", "Chiral analysis", "cap-stereochemistry", STR, r"chiral|stereochem", []),
 ("cap-mosher-marfey", "Mosher/Marfey derivatisation", "cap-stereochemistry", STR, r"mosher|marfey", []),
 ("cap-computational-stereo", "Computational stereochemistry", "cap-stereochemistry", STR, r"computational", []),
 # synthesis
 ("cap-total-synthesis", "Total synthesis", "cap-synthesis", SYN, r"full synthesis|total synthesis", []),
 ("cap-analogue-synthesis", "Analogue synthesis", "cap-synthesis", SYN, r"analogue", []),
 ("cap-fluorescent-analogues", "Fluorescent analogues", "cap-analogue-synthesis", SYN, r"fluorescent", []),
 ("cap-click-chemistry", "Click chemistry", "cap-synthesis", SYN, r"click", []),
 ("cap-isotope-labelling", "Isotope labelling", "cap-synthesis", SYN, r"isotope", []),
 ("cap-semi-synthesis", "Semi-synthesis / chemical modification", "cap-synthesis", SYN, r"chemical modification|semi-synth|modification of natural", []),
 ("cap-synthesis-feasibility", "Synthesis feasibility assessment", "cap-synthesis", SYN, r"success probability|synthesis target", []),
 ("cap-molecular-docking", "Molecular docking", "cap-computational-chemistry", SYN, r"docking", [("exact", EDAM.operation_0478)]),
 ("cap-qsar", "QSAR modelling", "cap-computational-chemistry", SYN, r"qsar", []),
 ("cap-chemical-modelling", "Chemical modelling", "cap-computational-chemistry", SYN, r"chemical modelling|modelling", []),
 ("cap-molecular-networking", "Molecular networking", "cap-computational-chemistry", SYN, r"molecular networking", []),
 ("cap-cheminformatics-libraries", "Chemical libraries / cheminformatics", "cap-computational-chemistry", SYN, r"chemical libraries|bioinformatics", []),
]
MT = {"exact": SKOS.exactMatch, "close": SKOS.closeMatch, "broad": SKOS.broadMatch, "related": SKOS.relatedMatch}
for slug, lab, broader, _, _, matches in CAPS:
    c = RES[slug]; g.add((c, RDF.type, EUR.Capability)); g.add((c, SKOS.prefLabel, L(lab)))
    g.add((c, SKOS.inScheme, RES["scheme-capabilities"]))
    if broader: g.add((c, SKOS.broader, RES[broader])); g.add((RES[broader], SKOS.narrower, c))
    else: g.add((c, SKOS.topConceptOf, RES["scheme-capabilities"]))
    for mt, iri in matches: g.add((c, MT[mt], iri))

# --------------------------------------------------------------------------- quantitative capacities (curated from text)
CAPACITY = {  # id: [(kind, min, max, unit, note)]
 "EUREMAP_007": [("qk-culture-volume", 0.001, 50, "LTR", "1 mL – 50 L cultivation scale")],
 "EUREMAP_008": [("qk-culture-volume", 0.5, 10, "LTR", "0.5–2 L bioreactors; scale-up to 10 L")],
 "EUREMAP_009": [("qk-culture-volume", None, 5, "LTR", "up to 5 L"), ("qk-extraction-mass", None, 100, "GRM", "up to 100 g")],
 "EUREMAP_010": [("qk-culture-volume", None, 20, "LTR", "up to 20 L")],
 "EUREMAP_011": [("qk-culture-volume", None, 5, "LTR", "up to 5 L")],
 "EUREMAP_012": [("qk-culture-volume", None, 5, "LTR", "up to 5 L")],
 "EUREMAP_013": [("qk-culture-volume", None, 5, "LTR", "up to 5 L")],
 "EUREMAP_014": [("qk-culture-volume", None, 40, "LTR", "cell pellets from cultures up to 40 L")],
 "EUREMAP_015": [("qk-extraction-mass", None, 10, "GRM", "up to 10 g")],
 "EUREMAP_016": [("qk-culture-volume", None, 5, "LTR", "up to 5 L")],
 "EUREMAP_017": [("qk-sample-requirement", None, 0.5, "MGM", "500 µg extract per assay")],
 "EUREMAP_022": [("qk-sample-requirement", 1, 10, "MGM", "1–10 mg extract")],
 "EUREMAP_028": [("qk-sample-requirement", None, 0.25, "MGM", "250 µg extract per assay")],
 "EUREMAP_037": [("qk-nmr-field", None, 500, "A56", "500 MHz NMR")],
 "EUREMAP_041": [("qk-nmr-field", None, 500, "A56", "500 MHz NMR")],
 "EUREMAP_043": [("qk-purification-yield", 1, 30, "MGM", "1–30 mg pure compound"), ("qk-input-extract-mass", None, 20, "GRM", "from 20 g extract")],
 "EUREMAP_045": [("qk-purification-yield", None, 100, "MGM", "up to 100 mg pure compound")],
 "EUREMAP_048": [("qk-purification-yield", None, 100, "MGM", "up to 100 mg purified compound")],
}
# explicit service-level inputs stated in the text
INPUT_RULES = [
 (r"culture media", "mat-culture-broth"), (r"extraction of biomass|biomass and culture|cell pellet", "mat-biomass"),
 (r"\bextracts?\b|of extract", "mat-crude-extract"), (r"purified compound|or compounds|compounds for", "mat-pure-compound"),
 (r"raw (dna sequencing )?reads", "mat-raw-reads"), (r"natural compounds", "mat-pure-compound"),
]

# --------------------------------------------------------------------------- services
rows = []
for r in S:
    sid = r["id"]; n = sid.split("_")[1]
    sv = RES[f"service-{sid}"]
    inst = institution(r["institution"], r["country"])
    islug = INST[r["institution"]][0]
    stepslug = STEPS[r["step"]][0]
    text_all = (r["title"] + " " + r["overview"]).lower()
    g.add((sv, RDF.type, EUR.Service))
    g.add((sv, DCT.identifier, Literal(sid)))
    g.add((sv, DCT.title, L(r["title"].rstrip("."))))
    if r["overview"]: g.add((sv, DCT.description, L(r["overview"])))
    g.add((sv, EUR.providedBy, inst))
    if r["unit"]: g.add((sv, EUR.deliveredByUnit, unit(r["unit"], inst, islug)))
    g.add((sv, EUR.atPipelineStep, step_nodes[stepslug]))
    for a in r["access"]: g.add((sv, EUR.hasAccessMode, RES[ACCESS[a][0]]))
    for ri in r["ri"]: g.add((sv, EUR.offeredThrough, RES[RIS[ri][0]]))
    g.add((sv, EUR.listedIn, CAT))
    g.add((sv, DCAT.landingPage, URIRef(f"https://services.euremap.eu/service/{sid.lower()}/")))
    g.add((sv, DCT.source, URIRef(f"https://services.euremap.eu/service/{sid.lower()}/")))
    if r["reference"]: g.add((sv, FOAF.page, URIRef("https://" + r["reference"])))
    g.add((sv, EUR.accessConditions, L(r["conditions"])))
    cond = r["conditions"].lower()
    fee = "fee-free" if cond.startswith("free") else ("fee-for-service" if "fee-for-service" in cond else "fee-on-request")
    g.add((sv, EUR.hasFeeModel, RES[fee]))
    g.add((sv, EUR.requiresPriorContact, Literal("contact" in cond, datatype=XSD.boolean)))
    if "ena" in cond: g.add((sv, EUR.requiresSubmissionTo, ENA)); g.add((sv, EUR.acceptsInput, RES["mat-raw-reads"]))
    if "Virtual" in r["access"]: g.add((sv, RDF.type, DCAT.DataService))
    # capabilities
    caps = []
    for slug, lab, broader, steps, rx, _ in CAPS:
        if rx and r["step"] in steps and re.search(rx, text_all):
            g.add((sv, EUR.hasCapability, RES[slug])); caps.append(slug)
    # software
    for lab, (slug, bt, rx) in SOFT.items():
        if re.search(rx, text_all + " " + r["reference"].lower()): g.add((sv, EUR.usesSoftware, RES[slug]))
    # explicit inputs (only within steps that consume material)
    if r["step"] in ("Chemical Extraction", "Bioassays & bioprofiling", "Safety & toxicity", "Chromatography", "Synthesis"):
        for rx, mat in INPUT_RULES:
            if re.search(rx, text_all) and (RES[mat], None, None) in g:
                if r["step"] == "Chemical Extraction" and mat not in ("mat-culture-broth", "mat-biomass"): continue
                g.add((sv, EUR.acceptsInput, RES[mat]))
    # capacities
    for i, (kind, mn, mx, unitc, note) in enumerate(CAPACITY.get(sid, [])):
        q = RES[f"capacity-{sid}-{i+1}"]
        g.add((sv, EUR.hasCapacity, q)); g.add((q, RDF.type, EUR.Capacity))
        g.add((q, EUR.quantityKind, RES[kind])); g.add((q, SCHEMA.unitCode, Literal(unitc)))
        if mn is not None: g.add((q, SCHEMA.minValue, Literal(mn, datatype=XSD.decimal)))
        g.add((q, SCHEMA.maxValue, Literal(mx, datatype=XSD.decimal)))
        g.add((q, RDFS.comment, L(note)))
    rows.append({"id": sid, "title": r["title"], "step": STEPS[r["step"]][1], "step_order": STEPS[r["step"]][2],
                 "phase": PHASES[STEPS[r["step"]][3]][0], "institution": INST[r["institution"]][1],
                 "acronym": INST[r["institution"]][2], "unit": UNIT_FIX.get(r["unit"], r["unit"]), "country": r["country"],
                 "access": ";".join(r["access"]), "research_infrastructure": ";".join(r["ri"]), "fee_model": fee,
                 "capabilities": ";".join(caps), "landing_page": f"https://services.euremap.eu/service/{sid.lower()}/"})

# --------------------------------------------------------------------------- national nodes (RI × country), derived
nodes = {}
for r in S:
    for ri in r["ri"]:
        nodes.setdefault((ri, r["country"]), set()).add(r["institution"])
for (ri, cname), insts in sorted(nodes.items()):
    a2 = COUNTRIES[cname][0]
    nd = RES[f"node-{RIS[ri][0][3:]}-{a2}"]
    g.add((nd, RDF.type, EUR.NationalNode)); g.add((nd, SKOS.prefLabel, L(f"{ri} – {cname}")))
    g.add((nd, EUR.nodeOf, RES[RIS[ri][0]])); g.add((nd, EUR.locatedInCountry, RES[f"country-{a2}"]))
    g.add((RES[RIS[ri][0]], ORG.hasUnit, nd))
    for i in insts: g.add((nd, EUR.nodeMember, RES[INST[i][0]]))
    g.add((nd, PROV.wasDerivedFrom, CAT))

g.serialize("data/euremap-catalogue.ttl", format="turtle")
with open("data/euremap-services.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print("triples:", len(g), "services:", len(rows), "nodes:", len(nodes))
for row in rows: print(row["id"], row["step"][:14], "|", row["capabilities"])
