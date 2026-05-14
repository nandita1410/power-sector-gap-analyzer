# TAXONOMY & CONSTANTS

POWER_TAXONOMY = {
    "Traditional Power Engineering": [
        "power systems","electrical engineering","substation","transformer","switchgear",
        "protection relay","short circuit","power factor","reactive power",
        "busbar","SCADA","DCS","PLC","HMI","RTU","energy audit",
        "grid","ETAP","PSS/E","power electronics"
    ],
    "Renewables & Energy Transition": [
        "solar PV","wind energy","wind turbine","battery storage","BESS","energy storage","rooftop solar","hybrid energy",
        "microgrid","VPP","virtual power plant","EV charging","green hydrogen",
        "electrolysis","geothermal","biomass","renewable energy",
    ],
    "Digital & Analytics": [
        "analytics","data analytics","machine learning","AI","artificial intelligence","IoT",
        "digital twin","predictive maintenance","bigdata","big data","python","MATLAB",
        "power BI","Tableau","cloud","AWS","Azure","GCP","cybersecurity","OT security",
        "DERMS","smart meter","smart meter analytics","smart meter data analytics","edge computing","blockchain","digital transformation",
        "simulation","data science","weather forecasting",
		"climate change",
		"wind speed forecasting",
		"climate change analysis",
		"rainfall forecasting",
		"humidity forecasting",
		"temperature forecasting",
        "smart meter",
        "agentic ai LLM",
        "smart meter data analytics",
        "smart meter analytics",
        "gen ai",
        "GE Predix",
        "Siemens PSS",
        "Ansys",
        "Simulink",
        "Azure Digital Twins",
    ],
    "Grid Modernization": [
        "smart grid","grid modernization","demand response","ancillary services","grid stability","HVDC",
        "SVC","STATCOM","PMU","synchrophasor","grid interconnection","grid optimization"
    ],
    "Project & Commercial": [
        "project management","PMP","EPC","O&M","feasibility study","financial modelling",
        "PPA","procurement","LOTO",
        "AutoCAD","MS Project",
    ],
    "Sustainability & Policy": [
        "ESG","carbon footprint","decarbonization","sustainability","GHG",
        "CDP","TCFD","SBTi"
    ],
}

ALL_SKILLS = [s for skills in POWER_TAXONOMY.values() for s in skills]

COUNTRY_META = {
    "us": {"name": "United States", "flag": "🇺🇸", "color": "#00d2ff"},    # Neon cyan
    "gb": {"name": "United Kingdom", "flag": "🇬🇧", "color": "#00ff87"},   # Neon green
    "au": {"name": "Australia",      "flag": "🇦🇺", "color": "#ffd700"},      # Neon gold
    "in": {"name": "India",          "flag": "🇮🇳", "color": "#f9718c"},          # Neon pink
    "de": {"name": "Germany",        "flag": "🇩🇪", "color": "#a75707"},      # Neon orange
    "ca": {"name": "Canada",         "flag": "🇨🇦", "color": "#f20505"},      # Neon red
    "offshore": {"name": "Offshore/Remote", "flag": "🌐", "color": "#a8b2c1"}, # Neutral grey for offshore
}
FIRST_WORLD = ["us", "gb", "au", "de", "ca"]

EMERGING_SKILLS = [
    "BESS","digital twin","green hydrogen","virtual power plant","HVDC","cybersecurity",
    "machine learning","IoT","DERMS","edge computing","synchrophasor","EV charging",
    "carbon credit","blockchain","predictive maintenance","AI","wide area monitoring",
    "smart meter","digital transformation","smart meter",
    "agentic ai LLM",
    "smart meter data analytics",
    "smart meter analytics",
    "gen ai",
    "consumption forecasting",
    "energy forecasting",
    "demand forecasting",
    "peak demand forecasting",
    "energy disintegration",
    "grid optimization",
    "GE Predix",
    "Siemens PSS",
    "Ansys",
    "Simulink",
    "Azure Digital Twins"
]

CAT_COLORS = {
    "Traditional Power Engineering": "#00d2ff", # Neon cyan
    "Renewables & Energy Transition": "#00ff87",# Neon green
    "Digital & Analytics":            "#ffd700",# Neon gold
    "Grid Modernization":             "#b15eff",# Neon purple
    "Project & Commercial":           "#00a8ff",# Electric blue
    "Sustainability & Policy":        "#00f5d4",# Neon teal
    "Other":                          "#8b949e",
}

# DEMO DATA — DEMAND

DEMO_JOBS = [
    {"source":"adzuna","country":"us","title":"Senior Grid Modernization Engineer","company":"NextEra Energy","description":"Masters degree required. Lead smart grid deployments SCADA DCS integration DERMS demand response IoT sensor networks predictive maintenance machine learning digital twin GE Predix Azure Digital Twins cybersecurity OT AWS cloud python HVDC synchrophasor PMU BESS energy storage battery storage grid stability wide area monitoring ancillary services frequency regulation ESG net zero."},
    {"source":"adzuna","country":"us","title":"Energy Storage Systems Engineer","company":"Tesla Energy","description":"Design commission BESS lithium ion battery management inverter controls virtual power plant VPP EV charging power electronics grid interconnection python ML analytics digital twin carbon credit ESG frequency regulation ancillary services blockchain energy storage cybersecurity AWS Azure."},
    {"source":"adzuna","country":"us","title":"Offshore Wind Technical Lead","company":"Orsted US","description":"Bachelors in electrical engineering. Offshore wind turbine HVDC transmission power systems load flow short circuit transformer protection relay machine learning predictive maintenance digital twin project management PMP ESG sustainability green hydrogen carbon footprint SBTi net zero AWS cloud python MATLAB data analytics."},
    {"source":"adzuna","country":"us","title":"Power Systems Data Scientist","company":"Eaton","description":"Machine learning anomaly detection python IoT edge computing big data cloud AWS Azure digital twin Ansys Simulink Siemens PSS SCADA power BI Tableau predictive maintenance grid stability smart meter AMI cybersecurity OT security synchrophasor artificial intelligence data analytics digital transformation."},
    {"source":"adzuna","country":"us","title":"Renewable Integration Specialist","company":"EPRI","description":"Grid modernization BESS battery storage virtual power plant VPP FACTS SVC STATCOM demand response ancillary services frequency regulation DERMS smart grid wide area monitoring PMU python MATLAB feasibility study PPA ESG net zero decarbonization sustainability."},
    {"source":"adzuna","country":"us","title":"OT Cybersecurity Engineer","company":"Dragos","description":"OT security cybersecurity ICS SCADA protection industrial control systems digital transformation AWS cloud IoT edge computing machine learning python data analytics power systems substation protection relay HSE regulatory compliance."},
    {"source":"adzuna","country":"gb","title":"Net Zero Grid Engineer","company":"National Grid ESO","description":"HVDC offshore wind battery storage BESS synchrophasor PMU machine learning digital twin virtual power plant ESG net zero carbon footprint SBTi green hydrogen smart grid demand response ancillary services cybersecurity OT python regulatory compliance TCFD climate risk decarbonization."},
    {"source":"adzuna","country":"gb","title":"Energy Transition Consultant","company":"Atkins","description":"Green hydrogen electrolysis offshore wind BESS EV charging decarbonization net zero ESG CDP carbon credit TCFD climate risk financial modelling IRR NPV PPA regulatory compliance just transition sustainability circular economy SBTi."},
    {"source":"adzuna","country":"gb","title":"Power Electronics Engineer","company":"GE Vernova","description":"Power electronics inverter converter HVDC offshore wind turbine BESS battery storage EV charging digital twin machine learning short circuit protection relay cybersecurity python MATLAB grid stability ESG sustainability."},
    {"source":"adzuna","country":"gb","title":"Smart Grid Solutions Architect","company":"Siemens Energy","description":"Smart grid SCADA DCS IoT edge computing cloud AWS Azure digital twin OT cybersecurity AMI smart meter DERMS demand response machine learning predictive maintenance big data python grid stability wide area monitoring PMU substation IED."},
    {"source":"adzuna","country":"gb","title":"Offshore Wind Project Manager","company":"RWE Renewables","description":"Masters in management. Offshore wind EPC project management PMP HSE HSSE procurement PPA financial modelling capex opex ESG sustainability carbon footprint regulatory compliance due diligence asset management O&M transformer substation net zero."},
    {"source":"adzuna","country":"gb","title":"Digital Energy Analyst","company":"Wood Mackenzie","description":"Data analytics python power BI Tableau machine learning AI digital twin IoT cloud AWS big data financial modelling IRR NPV PPA ESG carbon footprint decarbonization net zero TCFD climate risk regulatory compliance."},
    {"source":"adzuna","country":"au","title":"Renewable Energy Systems Engineer","company":"AGL Energy","description":"Solar PV battery storage BESS virtual power plant VPP EV charging smart grid demand response SCADA DCS inverter power electronics IoT python machine learning digital twin ESG net zero carbon footprint green hydrogen microgrid grid stability cybersecurity."},
    {"source":"adzuna","country":"au","title":"Energy Storage Lead Engineer","company":"Neoen Australia","description":"Battery storage BESS lithium ion frequency regulation ancillary services power electronics SCADA machine learning AI digital twin virtual power plant ESG sustainability PPA financial modelling project management PMP cybersecurity OT wide area monitoring."},
    {"source":"adzuna","country":"au","title":"Grid Stability Analyst","company":"AEMO","description":"Power systems load flow short circuit wide area monitoring PMU synchrophasor frequency regulation voltage regulation FACTS STATCOM HVDC machine learning python MATLAB smart grid demand response SCADA digital twin grid modernization cybersecurity OT."},
    {"source":"adzuna","country":"au","title":"Power Sector Digital Transformation","company":"Accenture","description":"Digital twin IoT edge computing cloud AWS Azure GCP machine learning AI big data python SCADA cybersecurity OT security smart meter AMI DERMS demand response blockchain ESG carbon footprint predictive maintenance project management digital transformation."},
    {"source":"adzuna","country":"au","title":"Green Hydrogen Project Engineer","company":"Fortescue","description":"Green hydrogen electrolysis fuel cell feasibility study financial modelling PPA EPC project management PMP HSE procurement capex opex IRR NPV ESG sustainability net zero SBTi decarbonization regulatory compliance due diligence."},
    {"source":"indeed_rss","country":"in","title":"Electrical Engineer Power Systems","company":"NTPC Limited","description":"B.Tech required. Power systems protection relay substation 132kV 400kV transformer switchgear load flow short circuit SCADA DCS PLC HMI earthing busbar circuit breaker energy audit grid distribution transmission power factor reactive power metering LOTO HSE ETAP."},
    {"source":"indeed_rss","country":"in","title":"Electrical Site Engineer","company":"Adani Power","description":"Substation commissioning transformer HV LV MV switchgear protection relay SCADA PLC earthing busbar circuit breaker 11kV 33kV metering energy audit load flow HSE LOTO procurement single line diagram cable sizing."},
    {"source":"indeed_rss","country":"in","title":"Solar Project Engineer","company":"Greenko Group","description":"Solar PV rooftop solar inverter SCADA earthing metering grid interconnection energy audit project management HSE procurement feasibility study single line diagram cable sizing."},
    {"source":"indeed_rss","country":"in","title":"Power Plant O&M Engineer","company":"Tata Power","description":"O&M power plant DCS PLC HMI SCADA transformer substation protection relay energy audit HSE LOTO metering switchgear busbar circuit breaker earthing."},
    {"source":"indeed_rss","country":"in","title":"Electrical Design Engineer","company":"L&T Power","description":"Electrical design substation protection relay transformer earthing load flow short circuit ETAP SCADA procurement HSE IEC standards AutoCAD single line diagram."},
    {"source":"indeed_rss","country":"in","title":"Wind Energy Technician","company":"Suzlon Energy","description":"Diploma in engineering. Wind turbine wind energy O&M SCADA protection relay grid earthing HSE LOTO metering preventive maintenance."},
    {"source":"indeed_rss","country":"in","title":"Power Sector Analyst","company":"Power Finance Corporation","description":"Financial modelling PPA regulatory compliance capex opex IRR NPV due diligence procurement feasibility study asset management tariff policy."},
    {"source":"indeed_rss","country":"in","title":"Distribution Engineer","company":"MSEDCL","description":"Distribution 11kV substation transformer protection relay metering energy audit HSE load flow earthing switchgear busbar circuit breaker."},
    {"source":"indeed_rss","country":"in","title":"Substation Engineer","company":"PGCIL","description":"Bachelors degree. Substation 400kV 132kV transformer switchgear protection relay SCADA IED earthing busbar circuit breaker HV metering energy audit HSE LOTO."},
    {"source":"indeed_rss","country":"in","title":"Lead Power Systems","company":"L&T","description":"Power systems load flow short circuit SCADA wind energy renewable energy python MATLAB simulation project management stakeholder feasibility study"},
    # --- TEST JOB ENTRY 1 (Foreign Country Mention) ---
    # This job is posted in India ('country': 'in'), but the description explicitly mentions 'New York, USA'.
    # Because of our logic, its skills appear under the 'US' demand, NOT 'India'.
    {"source":"test_source","country":"in","title":"Test Engineer","company":"Test Corp","description":"You will be based out of our office in New York, USA. Looking for experts in BESS and digital twin."},
    {"source":"test_source","country":"Offshore","title":"Test Engineer","company":"Test Corp","description":"You will be based out of our office in New York, USA. Looking for experts in BESS and digital twin."},
    # --- TEST JOB ENTRY 2 (Offshore Phrase) ---
    # This job is posted in India ('country': 'in'), but contains an offshore phrase.
    # Because of our new logic, its skills are labeled 'offshore' and NOT counted in 'India'.
    {"source":"test_source","country":"in","title":"Offshore Analyst","company":"Remote Solutions","description":"The client is from a different time zone. Not hiring for India local projects. Need skills in machine learning and Python."},
    
    # --- MORE OFFSHORE DEMO JOBS ---
    {"source":"test_source","country":"in","title":"Remote Smart Grid Engineer","company":"Global Power Co.","description":"You will be assigned to European projects. Requires smart grid, demand response, and grid modernization skills. Please note this is an offshore role."},
    
    {"source":"test_source","country":"in","title":"Data Scientist (Energy)","company":"Analytics Hub","description":"Our client is from a different time zone. Need expertise in data analytics, big data, artificial intelligence, and Tableau. Work hours align with US PST."},
    
    {"source":"test_source","country":"in","title":"OT Security Specialist","company":"CyberGrid","description":"We are explicitly not hiring for India domestic operations. All work is offshore. Requires cybersecurity, OT security, and SCADA expertise."}
]


# DEMO DATA — SUPPLY

DEMO_RESUMES = [
    {"name":"Rahul Sharma","experience_years":5,"education":"B.Tech EEE","location":"Delhi","text":"5 years power systems engineer NTPC. Expertise: substation design 132kV 400kV transformer switchgear protection relay coordination SCADA DCS PLC HMI load flow short circuit ETAP earthing busbar circuit breaker energy audit HSE LOTO."},
    {"name":"Priya Patel","experience_years":3,"education":"M.Tech Power","location":"Mumbai","text":"3 years renewable energy focus. Solar PV rooftop utility SCADA inverter earthing metering grid interconnection. AutoCAD. Currently learning python data analytics. Some exposure to BESS sizing."},
    {"name":"Amit Singh","experience_years":8,"education":"B.Tech EEE","location":"Bangalore","text":"8 years electrical design L&T EPC. Power systems protection relay substation transformer earthing load flow short circuit ETAP procurement HSE."},
    {"name":"Sneha Reddy","experience_years":2,"education":"B.Tech EEE","location":"Hyderabad","text":"2 years Greenko solar projects. Solar PV commissioning inverter SCADA monitoring grid interconnection earthing metering. Learning python pandas."},
    {"name":"Vikram Nair","experience_years":6,"education":"M.Tech Control","location":"Chennai","text":"6 years Hitachi Energy. Power quality SCADA substation protection relay grid SVC STATCOM. Some experience smart grid DERMS. Basic python scripting."},
    {"name":"Deepa Menon","experience_years":4,"education":"MBA Energy","location":"Delhi","text":"4 years Power Finance Corporation. Financial modelling PPA regulatory compliance capex opex IRR NPV due diligence procurement feasibility study asset management."},
    {"name":"Arjun Verma","experience_years":1,"education":"B.Tech EEE","location":"Pune","text":"1 year fresher Suzlon wind turbine O&M. Wind energy SCADA protection relay grid earthing HSE LOTO metering."},
    {"name":"Kavya Iyer","experience_years":7,"education":"M.Tech Power Systems","location":"Bangalore","text":"7 years Siemens Energy. Power systems SCADA smart grid grid modernization demand response DERMS PMU synchrophasor. Good exposure power BI. Some python."},
    {"name":"Rohit Gupta","experience_years":3,"education":"B.Tech EEE","location":"Noida","text":"3 years PGCIL substation engineer. Substation 400kV transformer switchgear protection relay SCADA IED earthing metering HSE LOTO."},
    {"name":"Ananya Das","experience_years":5,"education":"M.Tech Energy","location":"Kolkata","text":"5 years Tata Power. O&M DCS PLC HMI SCADA transformer substation protection relay HSE LOTO. Completed python basics. Solar PV wind energy interest."},
    {"name":"Suresh Kumar","experience_years":10,"education":"B.Tech EEE","location":"Hyderabad","text":"10 years BHEL. Power systems transformer substation protection relay load flow short circuit ETAP SCADA DCS PLC energy audit HSE. No digital skills."},
    {"name":"Meera Krishnan","experience_years":4,"education":"M.Tech EEE","location":"Bangalore","text":"4 years ABB India. Power electronics inverter converter SCADA substation protection relay transformer. Learning python machine learning. Interested BESS."},
    {"name":"Rajesh Pillai","experience_years":6,"education":"B.Tech Power","location":"Kerala","text":"6 years KSEB distribution. Distribution 11kV substation transformer protection relay metering energy audit HSE load flow earthing circuit breaker."},
    {"name":"Nisha Agarwal","experience_years":2,"education":"M.Tech Renewables","location":"Jaipur","text":"2 years Adani Solar. Solar PV BESS sizing grid interconnection feasibility study financial modelling PPA procurement. Python scripting data analytics power BI."},
    {"name":"Sanjay Rao","experience_years":9,"education":"B.Tech EEE","location":"Pune","text":"9 years Mahindra EPC. EPC project management PMP substation transformer protection relay SCADA procurement HSE capex opex feasibility study."},
]
