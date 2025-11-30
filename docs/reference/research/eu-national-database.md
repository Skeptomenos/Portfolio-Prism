# The European Regulated Data Landscape: An Analysis of National OAMs and the Irish Framework Preceding ESAP

## Section 1: Executive Summary & Direct Answer: The OAM Framework as the Precursor to ESAP

To directly answer the query: Yes, country-specific "alternatives" to the forthcoming European Single Access Point (ESAP) exist. They are, in fact, the legally mandated foundation of the current European transparency framework. These national databases are known as **Officially Appointed Mechanisms (OAMs)**.

The data for a regulated entity, such as an Irish-domiciled fund, can theoretically be sourced from its national OAM. However, as this report will detail, the practical architecture of the Irish framework—and the profound fragmentation across all Member States—makes this data retrieval process exceptionally complex and unreliable for systematic analysis.

The EU's Transparency Directive (2004/109/EC) mandates that each Member State must designate at least one OAM.1 The purpose of this OAM is to act as the central _storage_ facility for all "regulated information" disclosed by issuers whose home Member State it is.2 This regulated information includes periodic financial reports, such as Annual Financial Reports (AFRs) and Half-Yearly Financial Reports (HFRs), as well as information on major shareholdings and other inside information as defined by the Market Abuse Regulation (MAR).3

It is critical to clarify the relationship between the current OAMs and the future ESAP. The OAMs are the _current, fragmented system_ established in 2004. ESAP, by contrast, is the _future, centralized aggregator_ being built to resolve the deficiencies of this very system.1 ESAP, a key component of the 2020 Capital Markets Union (CMU) action plan, is scheduled for a phased rollout beginning by mid-2027. It will not replace the national OAMs; rather, it will _ingest_ data from them, providing a single, pan-European access point for the first time.1 The OAMs are the existing, disparate data silos; ESAP is the project to build the single, unified portal to search across all of them.

The core challenge for data analysts, and the central thesis of this report, is that the OAM network was designed primarily for _filing compliance_—that is, to provide a legal mechanism for an issuer to fulfill its duty to file. It was not designed for _public data retrieval_—that is, to provide an efficient, searchable, and harmonized database for investors, analysts, and the public.

This design philosophy is the root cause of the fragmentation and poor usability that data consumers currently face. Evidence of this can be found in early consultations from the Committee of European Securities Regulators (CESR), the precursor to the European Securities and Markets Authority (ESMA). A 2010 consultation paper discussed the mere _feasibility_ of requiring harmonized search facilities across the OAM network, such as common search keys for issuer name, ISIN, and type of regulated information.7 The fact that these basic search functions were a subject of consultation _after_ the network was established—rather than a core design requirement—proves that a user-friendly, pan-European search capability was not a primary objective. The network was constructed as 27 or more separate legal "filing cabinets," not an integrated data platform. ESAP 1 is the project to finally build this missing central catalog.

## Section 2: Deep Dive: The Irish Regulated Data Infrastructure (OAM Ireland)

The specific query regarding an "Irish database" highlights a particularly complex example of the OAM framework. To retrieve data from the Irish OAM, one must first understand its bifurcated structure, separating the regulator from the technical operator.

### The Irish Regulatory Dyad: Regulator vs. Operator

The Irish system for regulated information involves two distinct entities, a common point of confusion for data consumers:

1. **The Regulator:** The Central Bank of Ireland (CBI) is the single administrative competent authority for regulation and enforcement of the Transparency Directive in Ireland.2 It is the body responsible for ensuring issuers comply with their disclosure obligations.
    
2. **The OAM Operator:** The CBI has formally appointed the Irish Stock Exchange plc, which trades as **Euronext Dublin**, to _operate_ the OAM storage mechanism.2
    

This distinction is critical: the CBI _regulates and enforces_, while Euronext Dublin _operates the technical repository_ for storing the regulated information. An analyst seeking data must therefore look to the operator (Euronext Dublin), not the regulator (CBI).

### The Issuer-Facing Portal: Euronext Direct

For issuers, the process of filing information _into_ the Irish OAM is clear and well-defined. The primary interface is Euronext Direct, a secure, online portal designed for issuers to manage their regulatory obligations.11

This portal is a professional, issuer-centric compliance tool. Its "Announcements" service features a specific "PublishRISOAM" option.11 This function allows an issuer to simultaneously fulfill two separate legal obligations:

1. **RIS (Regulatory Information Service):** The timely _dissemination_ of market-moving news to the public.
    
2. **OAM (Officially Appointed Mechanism):** The _storage_ of this information in the official central archive.
    

The professional nature of this portal is further underscored by its other functions, which include applications for Legal Entity Identifiers (LEIs), filing of Net Asset Values (NAVs) for funds, and requests for ISIN codes.11

### The Public-Facing Portal: A Confounding Landscape

While the _filing_ mechanism for issuers is clear, the _retrieval_ mechanism for the public is confounded. Based on the available architecture, there is no single, dedicated public-facing portal for searching the _archive_ of OAM-stored documents in Ireland. This stands in sharp contrast to other jurisdictions, which are analyzed in Section 3.

Instead, the Irish public-facing component consists of several disparate and incomplete feeds:

1. **Live News Feeds:** The `live.euronext.com` portal provides _live_ stock exchange quotes and "regulated news".12 This is a _dissemination_ feed, analogous to a newswire. It is designed for timely disclosure of new information, not for historical research. An analyst cannot, for example, easily query this feed for all Annual Financial Reports published in the previous year.
    
2. **Euronext Corporate News:** Many of Euronext's "regulated information" links 13 point to corporate news and financial results for _Euronext NV_ (the listed parent company), not a comprehensive search tool for all issuers listed in Dublin.
    
3. **Third-Party Aggregators:** The Irish market ecosystem appears to rely heavily on third-party commercial services (such as Davy 14) or RNS aggregators (like Investegate 15) to consume, archive, and make sense of regulated market announcements.
    

### The "Irish Database" at the Central Bank (CBI)

A data analyst might logically turn to the regulator, the Central Bank of Ireland, to find the central database. However, this path also fails to yield the desired data.

- The CBI's "Corporate Reports" 16 and "Annual Reports" 16 sections contain the institutional reports _of the Central Bank itself_, not the regulated filings of listed issuers.
    
- Similarly, the CBI's "Funds" section provides extensive detail on the _rules_ governing UCITS (Undertakings for Collective Investment in Transferable Securities) and AIFs (Alternative Investment Funds) 19, including inward marketing requirements. However, it _does not_ provide a public database of the Annual or Half-Yearly reports filed by these funds.
    

### Key Assessment: "Storage" vs. "Searchable Access" in the Irish Model

The Irish OAM, operated by Euronext Dublin, successfully fulfills its legal mandate under the Transparency Directive to _store_ information.2 However, its public-facing component is almost entirely optimized for _timely dissemination_ through live news feeds 12, rather than _archival retrieval_ via a queryable database.

This architectural choice explains the precise difficulty reflected in the user query. An analyst knows that a regulated Irish-domiciled entity (like a major iShares or Xtrackers ETF) _must_ be filing its Annual Report with the Irish OAM. Yet, they are unable to locate a database from which to download this historical document. The Irish system is functionally bifurcated: a clear, professional-grade filing portal for issuers 11 and a live, newswire-style feed for the public. The "stored" archive, the OAM itself, is not exposed via a user-friendly search tool, rendering historical data retrieval exceptionally difficult.

## Section 3: Comparative Analysis: OAM Implementation in Key EU Member States

The challenge in Ireland is not unique; it is an exemplar of a wider, systemic fragmentation. To provide exhaustive detail, it is necessary to expand the analysis beyond Ireland to other major European financial centers. This comparison demonstrates the profound heterogeneity of the OAM landscape.

ESMA provides a central _list_ of hyperlinks to these national OAMs, but it does not aggregate the data itself.21 This list is the primary evidence of the system's fragmentation, as it reveals that OAMs are operated by entirely different _types_ of entities from one Member State to the next.

### Model 1: The Stock Exchange Operator (Luxembourg)

This model, similar to Ireland in its structure, offers a vastly different user experience.

- **Regulator:** Commission de Surveillance du Secteur Financier (CSSF).3
    
- **OAM Operator:** Luxembourg Stock Exchange (LuxSE).4
    
- **Filing Portal:** Issuers file using the "FIRST" (Financial Instruments Reporting Services Tool).6
    
- **Public Access Portal:** Crucially, LuxSE provides a dedicated, free, and public "OAM search" tool on its website.5 This portal is designed for analysts, offering clear filters for "issuer name," "country of issuer," "ISIN code," and "type of regulated information" (e.g., 'Annual financial report').5
    
- **Assessment:** This is the most user-friendly and logical model. It co-locates the listing, filing, and public search functions with a single, market-oriented operator that is incentivized to provide usable data to market participants.
    

### Model 2: The Government Registry Operator (Germany)

Germany employs a state-run, registry-based model.

- **Regulator:** Bundesanstalt für Finanzdienstleistungsaufsicht (BaFin).24
    
- **OAM Operator:** The Company Register (Unternehmensregister).21
    
- **Filing Portal:** Issuers file via the separate `publikations-plattform.de`.27
    
- **Public Access Portal:** The `unternehmensregister.de` website 28 serves as the central platform for _all_ company data, including OAM information.28 It provides a public search function with filters for "Accounting / financial reports" and "Fund information".30
    
- **Assessment:** This is a comprehensive, centralized model. However, its legal-entity focus, integrating regulated information with the _Handelsregister_ (Trade Register) 29, creates a different set of complexities, which are analyzed in Section 4.
    

### Model 3: The Official Journal Operator (France)

France utilizes a bifurcated model where the regulator and a government administrative body collaborate.

- **Regulator:** Autorité des Marchés Financiers (AMF).22
    
- **OAM Operator:** Direction de l'information légale et administrative (DILA), the state's official legal and administrative information directorate.21
    
- **Public Access Portal:** The official French OAM is `info-financiere.gouv.fr`.33 This portal provides both web access and an API for data reuse. The AMF also hosts its own search portal, the BDIF (Base de Données des Informations Financières).34
    
- **Assessment:** This government-led model separates the financial regulator (AMF) from the OAM data host (DILA).
    

### Model 4: The Central Bank / Depository Operator (Austria)

Austria's model is led by its central securities depository and control bank.

- **Regulator:** Finanzmarktaufsicht (FMA).
    
- **OAM Operator:** OeKB (Oesterreichische Kontrollbank AG).21
    
- **Filing Portal:** Issuers use the "OAM Issuer Info Upload" service.35
    
- **Public Access Portal:** The documentation for the Austrian OAM is heavily focused on the _issuer's obligation to upload_.35 While it states information is "made available again to the general public," the primary access point is not as clearly defined as in Luxembourg or Germany. Furthermore, attempts to access this portal during the research phase found the website to be inaccessible 36, highlighting significant usability and reliability issues.
    

### Key Assessment: Heterogeneity as a Systemic Flaw

The OAM framework is not one system; it is 27 or more different systems. The ESMA list 21 confirms the heterogeneity of the _types_ of entities chosen as operators:

- **Stock Exchanges** (e.g., Luxembourg, Cyprus)
    
- **Competent Authorities** (e.g., Belgium, Croatia, Hungary)
    
- **Company Registries** (e.g., Germany)
    
- **Official Journals** (e.g., France)
    
- **Central Depositories** (e.g., Austria)
    

This heterogeneity of _operators_ is the primary driver of the heterogeneity in _functionality_. An analyst cannot develop a single, programmatic data-sourcing methodology. They must learn 27 or more different, bespoke, and often-deficient interfaces, or pay a commercial data vendor who has undertaken the considerable effort to do so. This is the precise fragmentation that ESAP 1 is designed to resolve.

This comparative analysis is summarized in the table below.

---

#### Table 1: Comparative Framework of Key EU Officially Appointed Mechanisms (OAMs)

|**Member State**|**National Regulator (NCA)**|**Designated OAM Operator**|**Public Access Portal**|**Data Model**|
|---|---|---|---|---|
|**Ireland**|Central Bank of Ireland (CBI)|Euronext Dublin (ISE)|`live.euronext.com` (Live News)|**Exchange / Dissemination-Led:** Optimized for live news dissemination; lacks a public archival search database. 2|
|**Germany**|BaFin|Unternehmensregister (Company Register)|`unternehmensregister.de`|**Registry-Led:** Consolidates all legal company filings (financial, trade, gazette) in one central registry. 21|
|**France**|Autorité des Marchés Financiers (AMF)|DILA (Official Journal)|`info-financiere.gouv.fr`|**Government / Admin-Led:** A collaboration between the regulator (AMF) and the state's official publishing body (DILA). 21|
|**Luxembourg**|Commission de Surveillance du Secteur Financier (CSSF)|Luxembourg Stock Exchange (LuxSE)|`luxse.com` (OAM Search)|**Exchange / Market-Led:** Integrated, user-friendly, and public-facing search portal operated by the exchange. 4|
|**Austria**|Finanzmarktaufsicht (FMA)|OeKB (Oesterreichische Kontrollbank AG)|`oekb.at`|**Bank / Depository-Led:** Operated by the national control and services bank; public access is unclear and portal was found to be inaccessible. 21|

---

## Section 4: Critical Assessment: The Practical Deficiencies of the OAM Network

This report now moves from a theoretical description of the OAMs to a critical assessment of their practical usability for sourcing specific financial data. A series of test queries aimed at retrieving fund-level Annual Reports from the major OAMs universally failed, revealing a systemic design flaw.

### Case Study 1: Ireland – The "Missing" Database

- **Objective:** Find the Annual Report for a major, Ireland-domiciled UCITS ETF. A prime example is the iShares Core S&P 500 UCITS ETF, which is domiciled in Ireland 37 and has an Irish ISIN (IE00B5BMR087).
    
- **Result:** Failure. As established in Section 2, a functional, public-facing OAM _search database_ for Ireland could not be located. Public access is limited to "live news" feeds 12, which are unsuitable for historical, query-based research.
    

### Case Study 2: Luxembourg – The "User-Friendly" Portal Failure

- **Objective:** Find the Annual Report for a major, Luxembourg-domiciled UCITS ETF, such as the Xtrackers DAX UCITS ETF 1C (ISIN: LU0274211480, Domicile: Luxembourg).39 This test used the "best-in-class" LuxSE OAM search tool.5
    
- **Result:** Failure.5 Despite the portal 5 providing the correct, analyst-friendly filters (e.g., "Issuer name", "ISIN", "Type of regulated information"), the test search for "Xtrackers" returned no documents.
    

### Case Study 3: Germany – The Registry Portal Failure

- **Objective:** Find Annual or Semi-Annual reports for "Xtrackers" or its parent "DWS" on the German _Unternehmensregister_.28
    
- **Result:** Failure.30 The test search did not return the relevant UCITS fund reports.
    

### Case Study 4: France – The "Official" Portal Failure

- **Objective:** Find Annual Reports for major French asset managers "Amundi" or "Lyxor" on the `info-financiere.gouv.fr` OAM.
    
- **Result:** Failure.33 The test searches, even when using the provided filters for periodic information, did not yield the specific fund-level reports.
    

### Analysis: The Fundamental "Fund vs. Company" Mismatch

The universal failure of these OAMs to return _fund-level_ reports is not an intermittent bug; it is a _systemic design flaw_. The OAMs are, by and large, designed as _company registers_, not _fund databases_.

The structural logic proceeds as follows:

1. A financial analyst searches for a fund using its _product name_ (e.g., "iShares Core S&P 500 UCITS ETF") or its _product-level ISIN_ (e.g., IE00B5BMR087 38).
    
2. A registry-style OAM, such as Germany's _Unternehmensregister_ 28 or France's `info-financiere.gouv.fr` 33, is structured around _legal entities_.
    
3. The _legal entity_ or "Issuing Company" for this iShares ETF is "iShares VII plc".37 The ETF itself is merely a _sub-fund_ of this Irish-domiciled _umbrella_ structure.
    
4. The Annual Report is therefore filed under the legal entity name, "iShares VII plc."
    
5. Consequently, the analyst's search fails. The OAM's search index for "Issuer Name" 5 maps to the legal umbrella entity, _not_ the sub-fund product name or the sub-fund ISIN.
    

This critical, structural mismatch explains the universal failures across all tested OAMs.5 The OAMs are functioning correctly as legal repositories at the _umbrella entity_ level, but analysts are searching for data at the _sub-fund/product_ level. This disconnect makes them functionally useless for this common and critical use case.

### Compounding Factor: The Fund Domicile "Shell Game"

This structural problem is compounded by the fluid nature of fund domiciles. An analysis of Xtrackers ETFs, for example, reveals a common trend of "now closed Luxembourg domiciled sub-fund[s]" being restructured and moved to a new _Irish_ domicile.41

This migration, often pursued for tax efficiency or regulatory streamlining, adds another layer of complexity for the data analyst. To find a historical report, an analyst must first track the fund's legal domicile _over time_ simply to determine _which_ national OAM (Luxembourg or Ireland) to begin their (already flawed, umbrella-level) search.

## Section 5: Concluding Analysis: Data Harmonisation (ESEF) and the Future (ESAP)

The European Union is aware of the profound deficiencies identified in this report. Its response is a two-part solution designed to solve the problems of both data _format_ and data _access_.

### Part 1: The Common Format (ESEF)

The EU's first step was to harmonize the _format_ of the data being filed. The European Single Electronic Format (ESEF) is now mandatory for Annual Financial Reports (AFRs) for fiscal years beginning on or after 1 January 2020.1

This mandate requires issuers to prepare their AFRs in XHTML (eXtensible HyperText Markup Language), which makes them human-readable in any standard web browser.1 Furthermore, where such reports contain consolidated financial statements prepared under IFRS, they must embed iXBRL (inline eXtensible Business Reporting Language) tags.1 This tagging makes the key financial data machine-readable, enabling automated analysis.4

ESEF created a _common language_ for financial reporting. In effect, all the "books" (AFRs) in the 27 national "libraries" (OAMs) are now written in the same language. However, this did not solve the problem of _access_. An analyst still had to travel to 27 different libraries, each with a different (or, in Ireland's case, non-existent) card catalog, to find these books.

### Part 2: The Common Access Point (ESAP)

This is the user's "ESAP" and the EU's final solution to the access problem. ESAP is _not_ a new OAM, nor will it replace the national OAMs. It is conceived as a single, pan-EU _aggregator_ that will sit _on top_ of the existing national infrastructure.1

ESAP will ingest the ESEF-formatted, iXBRL-tagged data from all the national OAMs (as well as from other registries) and, for the first time, provide a single, harmonized, and queryable search interface for all public regulated information in the EU.1 This will, in theory, solve the fragmentation problem.

### Final Report Conclusion

The query "Are there country specific alternatives to ESAP?" and the specific challenge of finding an "Irish database" are the precise business case _for_ ESAP.

The "alternatives"—the national OAMs—exist, but they constitute a fragmented, non-harmonized, and, for many analytical purposes, practically dysfunctional network. This report identifies two primary, systemic failures:

1. **A "Filing vs. Retrieval" Design:** The OAMs were largely designed as legal "filing cabinets" to satisfy issuer compliance, not as public-facing "databases" for data retrieval. This is exemplified by the Irish model, which provides a clear issuer portal (`Euronext Direct`) 11 but no corresponding public search archive, offering only a "live news" feed.12
    
2. **A "Company vs. Fund" Mismatch:** The OAMs are structured around _legal entities_ (e.g., "iShares VII plc" 37), while analysts search for _financial products_ (e.g., "iShares Core S&P 500 ETF" 38). This structural disconnect renders even the most user-friendly OAMs (like Luxembourg's) ineffective for retrieving fund-level reports.5
    

The user's difficulty in obtaining data from the Irish OAM is not an isolated problem; it is the exemplar of a systemic, EU-wide data infrastructure failure.

A systematic, cross-border, and product-level data retrieval strategy is not practically feasible under the current OAM framework. This specific, high-friction problem for investors and analysts is what the European Single Access Point (ESAP) is being built, with a target date of mid-2027, to finally solve.1 Until ESAP is operational, data consumers must rely on a combination of high-friction manual searches at the _legal entity_ level on disparate national OAMs or procure this data from commercial vendors who have already undertaken this complex aggregation.