field:
  - name: "Computational Biology"
    description: "Application of computational methods, machine learning, or statistical approaches to biological problems"
    points: 1
    subcategories:
      - name: "Network Biology"
        description: "Analysis of biological systems using network/graph theory, including protein-protein interaction networks, gene regulatory networks, or systems biology approaches"
        points: 3
      - name: "Statistical Genetics"
        description: "Statistical methods for analyzing genetic data, including GWAS, polygenic risk scores, heritability estimation, or genetic association studies"
        points: 2
      - name: "Cancer Biology"
        description: "Computational or systems approaches to understanding cancer biology, tumor heterogeneity, or cancer genomics"
        points: 2
      - name: "Genomics Language Models"
        description: "Language models, transformers, or deep learning approaches trained on genomic sequences (DNA, RNA, protein)"
        points: 2
  - name: "No relevant field or subfield"
    description: "Articles that do not fall into any of the preferred computational biology subfields"
    points: -3

applications:
  - name: "Drug Discovery"
    description: "General drug discovery research, including drug screening, lead optimization, or pharmacology"
    points: 1
    subcategories:
      - name: "Drug Target Discovery"
        description: "Identifying and validating therapeutic targets for diseases, disease gene prioritization, or target-disease associations"
        points: 3
      - name: "Trends in Pharma"
        description: "Industry trends, pharmaceutical R&D strategies, market analysis, or regulatory perspectives in drug development"
        points: 3
  - name: "Biomarker discovery"
    description: "Identification or validation of diagnostic, prognostic, or predictive biomarkers for diseases"
    points: 1
  - name: "Other application"
    description: "Applications outside the preferred areas (clinical ML, agriculture, environmental biology, etc.)"
    points: -2
    subcategories:
      - name: "Only non-human application(s)"
        description: "Studies exclusively focused on non-human organisms (plants, model organisms, microbes) with no clear human disease relevance"
        points: -5

preferred_article_types:
  - name: "Review"
    description: "Comprehensive review articles, meta-analyses, or systematic reviews that synthesize current knowledge in a field"
    points: 3
  - name: "Methodological Guidelines"
    description: "Best practices, benchmarking studies, standardization recommendations, or tutorials for applying methods"
    points: 2
  - name: "New Computational Method"
    description: "Novel algorithms, software tools, databases, or computational frameworks introduced for the first time"
    points: 1
  - name: "Comment"
    description: "Commentaries, perspectives, or opinion pieces discussing recent findings or field directions"
    points: 1
  - name: "Large-Scale Analyses"
    description: "Studies involving large datasets, multi-cohort analyses, or comprehensive genomic/proteomic characterizations"
    points: 1
  - name: "Pre-print"
    description: "Manuscripts posted on preprint servers (bioRxiv, medRxiv, arXiv) that have not yet undergone peer review"
    points: -1
  - name: "Corrigendum"
    description: "Corrections, errata, or retractions of previously published articles"
    points: -4

preferred_journals:
  - name: "Foundations and Trends in Machine Learning"
    description: "High-quality monograph series providing comprehensive surveys of machine learning topics"
    points: 3
  - name: "Nature Genetics"
    description: "Premier journal for genetics and genomics research with high impact findings"
    points: 2
  - name: "Nature Reviews Drug Discovery"
    description: "Leading review journal covering all aspects of drug discovery and development"
    points: 3
  - name: "Trends in Genetics"
    description: "Review journal providing accessible overviews of current trends in genetics research"
    points: 1
