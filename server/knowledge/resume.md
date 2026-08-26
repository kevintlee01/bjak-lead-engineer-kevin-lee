
# Kevin Lee — Resume

## Contact & Location

Location: San Francisco Bay Area, California, USA
LinkedIn: linkedin.com/in/kevintlee01
GitHub: github.com/kevintlee01

Note: manager/supervisor names and exact street addresses have been redacted from this document for privacy. City, state/province and country are kept.

## Education

- Master of Engineering, Electrical Engineering, University of Toronto, Toronto, Ontario, Canada — Sep. 2014 - Nov. 2015. Specialization: VLSI and Integrated Circuits (Digital & Analog Design), Semiconductor Physics and Micro-/Nano-Fabrication.
- Bachelor of Applied Science, Electrical Engineering, Minor in Engineering Business, University of Toronto, Toronto, Ontario, Canada — Sep. 2009 - Jun. 2014. Specialization: VLSI and Integrated Circuits, Semiconductor Physics and Micro-/Nano-Fabrication, Computer Architecture & Computer Hardware.
- High School Diploma with Honors, Fraser Heights Secondary School, Surrey, British Columbia, Canada — Sep. 2004 - Jun. 2009.

## Technical Skills

- Application Software: Microsoft Office Suite, Adobe Creative Suite, MATLAB & Simulink, IntelliJ, PyCharm, Visual Studio, Android Studio, Atlassian JIRA, Eclipse IDE
- AI & LLM Engineering: Agentic AI, LangChain, Retrieval-Augmented Generation (RAG), Vector Databases, Prompt Engineering, Fine-Tuning
- EDA Tools: Cadence (Virtuoso, Encounter, Allegro, OrCAD), Synopsys (HSPICE, Design Compiler, Sentaurus, PrimeTime), Mentor Graphics ModelSim, Micro Magic Design, LTSpice, Altera Design Suite, Libero SoC, SoftConsole
- Computer Languages: C, C++, Java, JavaScript, Node.js, Scala, Verilog, Verilog-AMS, SystemVerilog, Assembly, Perl, Python, SKILL, Groovy, LaTeX, HTML
- Frameworks & Architecture: Microservices, Play Framework, RESTful API design
- Software Tools: Jenkins, Airflow, Docker, Apache, Kafka, Kubernetes (K8s), Google Cloud Platform (GCP), Google Ad Manager
- Databases: MySQL, MongoDB, Postgres, BigQuery
- Operating Systems: Microsoft Windows, UNIX (Mac OS X, Linux, Solaris)
- Spoken Languages: English, French, Chinese

## Employment: Senior Software Engineer — Advertisement Billing in eCommerce

Company: Walmart Incorporated, Sunnyvale, California, USA
Dates: Sep. 7, 2024 - Present

- Built an Agentic AI agent that autonomously diagnoses and resolves production incidents end-to-end, from Jira intake to verified fix, replacing ~45 min of manual on-call triage with a 5-minute automated pipeline (roughly an 85% cut in resolution time)
- Engineered a safety-first execution model where the agent self-classifies every action it takes via a 4-tier safety model, blocks dangerous operations, and pauses for human approval — trusted to run autonomously on ~70% of live incidents
- Designed the platform to scale across Walmart and Sam's Club, integrating 8+ production systems through a pluggable MCP layer with a RAG pipeline over a pgvector store for runbook and past-incident retrieval, where each team onboards within 15 min using a single JSON config
- Took full ownership of all Airflow advertisement billing ETL pipelines orchestrating data movement across BigQuery and Postgres to generate >$300M in monthly invoices (~$3.6B annualized)
- Championed the implementation of CI/CD pipelines enabling automated pre-commit unit and integration testing across all repositories
- Led the strategic migration and consolidation of the Airflow billing repository in collaboration with the AdTech Infra team
- Engineered the credit memo and rebill functionality as the sole contributor managing implementation, testing and release for critical financial adjustment services
- Optimized system reliability by configuring advanced Grafana dashboards and automated alerting for billing environments
- Championed AutoCRQ enablement for Airflow jobs, gathering requirements and driving the approval process
- Spearheading the architecture of a bespoke data integration for the company's largest advertising partner (>$75 million in annual spend), delivering customized REST API and SFTP solutions
- Directing the technical roadmap and end-to-end integration of financial data streams for premier high-revenue accounts

## Employment: Software Engineer III — Advertisement Campaigns in eCommerce

Company: Walmart Incorporated, Sunnyvale, California, USA
Dates: Jul. 12, 2021 - Sep. 6, 2024

Note (known discrepancy, kept intentionally rather than silently smoothed over): this role and the Senior Software Engineer role above are the same continuous Walmart tenure. This document records them as two distinct titles with a promotion boundary at Sep 2024. An earlier, condensed one-page draft of this resume compressed both into a single line item, "Senior Software Engineer & AI Team Lead — Advertisements & Billing, 2021 - Present." When asked about title or start date, state both versions and flag the discrepancy rather than silently picking one.

- Led end-to-end architecture of a new advertisement campaign service, directing a team of 3 engineers (1 intern, 2 junior), managing >$10 billion in first- and third-party advertiser campaigns while reducing operating costs by $26 million
- Interfaced the new API with a partially-schemaless MongoDB to map common fields while allowing field flexibility
- Facilitated cross-functional design meetings to identify consumer use cases, improving performance by over 70%
- Integrated & onboarded multiple third party advertisement platforms contributing over $25 million in annual revenue
- Eliminated data storage cost of $1 million per year via hive metastore cleanup automation using Jenkins jobs
- Identified and resolved a MySQL DB to Hive metastore DB race condition for old partitions removal
- Took ownership of contextual targeting workflow and managed new incoming taxonomy and placement requests
- Implemented deduplication keys to prevent identical advertisements from appearing on the same web page
- Aided in Jenkins job migration to new cloud provider while enhancing security by moving passwords to a vault

## Employment: Software Engineer

Company: Intel Corporation, Santa Clara, California, USA
Dates: Aug. 17, 2020 - Aug. 27, 2021

- Designed a microservice for managing and tracking department-owned servers using Node.js with React.js, GraphQL, and a Docker container for MySQL data
- Addressed efficiency issues of server management by creating Python programs reducing workflow by 98%
- Managed and distributed work across intern teams, building multi-project Gantt charts in Microsoft Project to track resource allocation and level-of-effort across parallel workstreams
- Spearheaded departmental adoption of new infrastructure tools by onboarding and training 6+ system admins

## Employment: Component Design Engineer

Company: Intel Corporation, Santa Clara, California, USA
Dates: Jul. 23, 2018 - Aug. 16, 2020

- Defined a new back end Place & Route methodology reducing full chip and block assembly errors by 90%
- Coordinated all partition physical verification reviews to achieve closure in preparation for tapeout
- Developed several efficient algorithm-focused Perl & Python scripts to verify data prior to tapeout

## Employment: Design Automation Engineer

Company: Intel Corporation, Santa Clara, California, USA
Dates: Jan. 16, 2018 - Jul. 22, 2018

- Defined entire back end physical verification and handoff flow, reducing workflow from 2 days to 1 hour
- Managed and distributed work evenly among interns working on back end place & route related flows
- Expedited integrated circuit & silicon photonics CAD tools, PDK, and runset issues with JIRA Agile
- Collaborated with external vendors on rule deck modifications and 3rd party IP integration

## Employment: Senior CAD Layout Engineer

Company: Intel Corporation, Santa Clara, California, USA
Dates: Jun. 19, 2017 - Jan. 15, 2018

Note: this role immediately precedes the Design Automation Engineer role above at the same Intel site, sharing the same back end place & route responsibilities across the title change.

- Defined entire back end physical verification and handoff flow, reducing workflow from 2 days to 1 hour
- Managed and distributed work evenly among interns working on back end place & route related flows
- Expedited integrated circuit & silicon photonics CAD tools, PDK, and runset issues with JIRA Agile
- Collaborated with external vendors on rule deck modifications and 3rd party IP integration

## Employment: ASIC Design Engineer II — Physical Design Verification Engineer (Full Chip)

Company: Apple Incorporated, Cupertino, California, USA
Dates: Sep. 21, 2015 - Mar. 29, 2017

- Oversaw and supported 3 product and 2 test chip designs from floorplan to tapeout
- Drove cross-functional meetings involving FE netlist, power, analog/RF, P&R, ESD, CAD and package teams
- Reduced product chip's total area by 1.5mm2 for a pad-limited design while lowering power leakage
- Reduced GPIO, bump and RDL generation and handoff flow runtime from 1 week to 5 hours
- Collaborated with foundry on next generation technology nodes to meet custom library specifications

## Employment: Process Design Kit Engineer (Intern)

Company: Taiwan Semiconductor Manufacturing Company, Limited (TSMC), Hsinchu, Taiwan
Dates: Jun. 23, 2014 - Aug. 31, 2014

- Enhanced 16nm & 10nm FinFET devices by identifying errors using Cadence Virtuoso GXL
- Initiated a unified Perl script project for extracting HSPICE, Spectre and Eldo model cards' syntax
- Resolved incompatible model cards with unified script, improving PDK development time by 80%

## Employment: R&D Engineer (Intern)

Company: Microsemi (Actel) Corporation, San Jose, California, USA
Dates: Jul. 2, 2012 - Jul. 26, 2013

- Minimized latch-up on an SoC FPGA in a radiation environment by over 50% with additional well-taps
- Mentored team members in Cadence Virtuoso XL and minimal metal line parasitics practices
- Piloted a software-hardware project to improve data monitoring by 90% during off-site radiation tests

## Academic Teaching & Course Development Roles (University of Toronto)

- Digital Systems Course Developer — May. 2015 - Aug. 2015
- Computer Hardware Teaching Assistant — Jan. 2015 - Apr. 2015
- Digital Systems Teaching Assistant — Sep. 2014 - Dec. 2014
- VLSI Systems & Design Course Developer — May 2012 - Jun. 2012

## Earlier Work & Volunteer Experience

- Room Inspector, University of Toronto New College Residence — Apr. 2012 - May 2012
- Product Tester, Best Buy Corporation, Langley, British Columbia, Canada — May 2011 - Aug. 2011
- Computer Engineer Intern, Progressive Intercultural Community Services Society, Surrey, British Columbia, Canada — May 2010 - Aug. 2010
- Pharmacy Assistant, Fraser Heights Pharmacy, Surrey, British Columbia, Canada — Mar. 2005 - Apr. 2008
- Laboratory Assistant, Bodycote Testing Group, Surrey, British Columbia, Canada — Jun. 2007 - Aug. 2007
- Senior Caretaker, Kinsmen Place Lodge, Surrey, British Columbia, Canada — Sep. 2008 - Aug. 2009
- Volunteer Coordinator, City of Surrey Parks Lend-A-Hand — Sep. 2008 - Jun. 2009
- Library Monitor Leader, Fraser Heights Secondary School Library — Feb. 2006 - Jun. 2009
- Christmas Gift Wrapper, The Centre for Child Development — Nov. 2005 - Dec. 2008
- Reading Buddy, Guildford Library — Oct. 2006 - Nov. 2008

## Engineering Projects

- Ticketing Web Application (GitHub, Jul. 2022 - Jan. 2023): full-stack developer; web app for uploading, selling and purchasing tickets; microservices for login, order creation, ticketing and payments on individual clusters.
- Server Documentation Web Forum Microservices (Intel Corporation, Spring 2021): Node.js/React microservice with GraphQL and Dockerized MySQL for server tracking; login, web forum, and reboot services.
- Microservices Application - Online Forum (GitHub, Spring 2021): online forum in Node.js/React with MySQL in Docker; RESTful interface with account creation, auth, and GraphQL testing.
- Web Scraper Application - Currency Converter (GitHub, Spring 2021): Python web scraper for live currency conversion with a cross-platform GUI.
- RESTful Web Service - Student Database (GitHub, Spring 2021): Java Spring Boot RESTful service with PostgreSQL and an HTML interface for POST/GET.
- Android Application - Earthquakes (GitHub, Winter 2020): retrieved earthquake JSON from a web API, listed results, and mapped coordinates onto Google Maps by magnitude.
- High-Speed I/O Design for Pixel-Programmable CMOS Image Sensor (University of Toronto, Summer 2015): LVDS transmitter/receiver design in AMS 0.35um for tapeout; 1.0Gbps post-layout simulation speed.
- VLSI Design Flow of L1 and L2 Cache with MSI Protocol Handling (University of Toronto, Fall 2014): project leader; 16KB/32KB cache design in TSMC 65nm using Cadence Virtuoso, Synopsys Design Compiler and Cadence Encounter.
- Model Card & Netlist Centralized Parsing System (TSMC, Summer 2014): project leader; Perl script identifying first/follow sets from grammars for model card parsing across technology nodes.
- Self-Powered Autonomous Recharging for Quadcopters (SPARQ) (University of Toronto, 2013 - 2014): power-management circuitry and battery monitoring firmware for autonomous docking and recharging of UAVs.
- Effective Interfacing of Java Software to GPIB Hardware (Microsemi Corporation, 2012 - 2013): project leader; Java UI programs to control GPIB power supplies and oscilloscopes, deployed at radiation test sites.
- 4-bit Microprocessor VLSI Design Flow (University of Toronto, Spring 2012): CMOS 4-bit AMD 2901 microprocessor datapath, schematic and custom layout.
- Automated Storage & Retrieval System (University of Toronto, Spring 2011): project leader; Morse-code communication interface between an 8-bit microcontroller and a 32-bit Nios II FPGA processor, driving a LEGO retrieval machine.
- Reaching Beyond Moore's Law: Graphene for VLSI (University of Toronto, Fall 2014): independent; presented semiconductor physics of graphene versus silicon and methods of turning its semi-metal band structure into a band gap.
- Programmable Gain Operational Transconductance Amplifier (University of Toronto, Fall 2014): independent; designed and modeled a fully differential, programmable gain amplifier using HSPICE netlists, achieving 80MHz bandwidth and 75-degree phase margin tunable to gains of 1-16 with 1% accuracy.
- Operational Amplifier Integrated Circuit Design (University of Toronto, Fall 2013): project member; schematic and layout design of a two-stage operational amplifier with negative feedback in STMicroelectronics' 90nm technology using Cadence Virtuoso.
- Server Design Project (University of Toronto, Spring 2011): team leader; UNIX-based server in C allowing multiple users to securely remote-access disk data storage, with TCP network connect and data storage testing.
- Digital Logics Accelerometer Project (University of Toronto, Fall 2010): project leader; tri-axis accelerometer on an FPGA in Verilog with SPI-4 wire control, plus an LED clock to time rate of change.
- Accelerometer Gravity Simulator (University of Toronto, Spring 2011): independent; tri-axis accelerometer on an FPGA in Verilog with SPI-4 wire control, displaying readings on 7-segment HEX displays.
- Bendale Acres Senior Home Redesign (University of Toronto, Spring 2010): project member; assessed hazards in a senior home's garden and produced a final design report with labeled dimensions for improvements.
- City of Toronto Bike Rack Redesign (University of Toronto, Fall 2009): project member; citywide public bike rack redesign focused on theft-resistant locking and modern urban aesthetics.

## Certifications

- IBM Generative AI Engineering Professional Certificate, IBM — May 2026
- IBM Full Stack Software Developer Professional Certificate, IBM — May 2026
- Google Advanced Data Analytics Professional Certificate, Google — May 2026
- Google Business Intelligence Professional Certificate, Google — Apr. 2026
- Google Data Analytics Professional Certificate, Google — Apr. 2026
- Medical Terminology Specialization, Rice University — Apr. 2026
- Introductory Human Physiology, Duke University — Apr. 2026
- Microsoft Excel Professional Certificate, Microsoft — Apr. 2026
- Leading People and Teams Specialization, University of Michigan — Apr. 2026
- Google Cybersecurity Professional Certificate, Google — Apr. 2026
- Google Project Management Professional Certificate, Google — Apr. 2026
- Financial Markets, Yale University — Apr. 2026
- IBM RAG and Agentic AI Professional Certificate, IBM — Mar. 2026
- Google People Management Essentials Specialization, Google — Mar. 2026
- Google AI Professional Certificate, Google — Mar. 2026
- The Science of Well-Being, Yale — Mar. 2026
- Microservices with Node JS and React, Udemy — Jan. 2023

## Awards & Achievements

- Global Tech Hackathon Finalist (Top 20 of 2336 Projects), Walmart Incorporated — 2026
- Make The Difference (MTD) Award, Walmart Incorporated — 2025
- Make The Difference (MTD) Award, Walmart Incorporated — 2023
- Intel Customer Satisfaction Award, Intel Corporation — 2020
- CADO 2017 Role Model Award, Intel Corporation — 2018
- Top Capstone Design Project Award, University of Toronto — 2014
- Technology & Development Department Award, Microsemi Corporation — 2013
- Water Safety Instructor, LIT Aquatics — 2009
- Career Diploma in Applied Sciences, Fraser Heights Secondary School — 2009
- Career Diploma in Health and Human Services, Fraser Heights Secondary School — 2009
- Leadership Award, Fraser Heights Secondary School — 2009
- National Book Award, University of Toronto — 2009
- 2nd Place, Crystal Growing Competition, The Chemical Institute of Canada — 2008
- Work Experience 12 Plaque, Fraser Heights Secondary School — 2008
- Major Service Award, Fraser Heights Secondary School — 2008
- National Lifeguard Service, LIT Aquatics — 2008
- Standard First Aid & CPR Level C, LIT Aquatics — 2008
- Violin Practical Level 8, Royal Conservatory of Music — 2007
- Rudiment Level 2, Royal Conservatory of Music — 2007

## Extra-Curricular Activities

- Emergency Responder, Emergency Response Team, Walmart Incorporated — 2024 - Present
- Regional Ambassador, Engineering Alumni Network, University of Toronto — 2022 - Present
- Mentor, Alumni Mentorship Program, University of Toronto — 2016 - Present
- Alumni Network Coordinator, Friends of Design, University of Toronto — 2011 - Present
- Medical Emergency Responder, Emergency Response Team, Intel Corporation — 2018 - 2021
- Advanced Medical Emergency Responder (AMERT), Apple Incorporated — 2016 - 2017
- Developer, Arduino Development Projects, Arduino Open Source Development — 2011 - 2013
- Network Representative, New College Residence, University of Toronto — 2010 - 2012
- VP Internal, Sustainable Engineers Association, University of Toronto — 2010 - 2011
- President, Environmental Club, Fraser Heights Secondary School — 2008 - 2009
- President/Founder, Science Club, Fraser Heights Secondary School — 2008 - 2009
- Regional/School Correspondent, S.M.A.R.T.S., Youth Science Canada — 2008 - 2009
- Member, Grad Committee, Fraser Heights Secondary School — 2008 - 2009
- Member, Student Council, Fraser Heights Secondary School — 2007 - 2009
