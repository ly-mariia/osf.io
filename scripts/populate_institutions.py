#!/usr/bin/env python3
"""Populate development database with Institution fixtures."""

import argparse
import logging
import sys
from urllib.parse import quote

import django
from django.db import transaction

django.setup()

from website import settings
from website.app import init_app
from osf.models import Institution
from website.search.search import update_institution

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

ENVS = ["prod", "stage", "stage2", "stage3", "test", "local"]

# TODO: Store only the Entity IDs in OSF DB and move the URL building process to CAS
SHIBBOLETH_SP_LOGIN = (
    f"{settings.CAS_SERVER_URL}/Shibboleth.sso/Login?entityID={{}}"
)
SHIBBOLETH_SP_LOGOUT = (
    f"{settings.CAS_SERVER_URL}/Shibboleth.sso/Logout?return={{}}"
)

# Using optional args instead of positional ones to explicitly set them
parser = argparse.ArgumentParser()
parser.add_argument(
    "-e",
    "--env",
    help="select the server: prod, test, stage, stage2 or stage3",
)
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "-i", "--ids", nargs="+", help="select the institution(s) to add or update"
)
group.add_argument(
    "-a", "--all", action="store_true", help="add or update all institutions"
)


def encode_uri_component(val):
    return quote(val, safe="~()*!.'")


def update_or_create(inst_data):
    inst = Institution.load(inst_data["_id"])
    if inst:
        for key, val in inst_data.items():
            setattr(inst, key, val)
        inst.save()
        print(f"Updated {inst.name}")
        update_institution(inst)
        return inst, False
    else:
        inst = Institution(**inst_data)
        inst.save()
        print(f"Added new institution: {inst._id}")
        update_institution(inst)
        return inst, True


def main(default_args=False):
    if default_args:
        args = parser.parse_args(["--env", "test", "--all"])
    else:
        args = parser.parse_args()

    server_env = args.env
    update_ids = args.ids
    update_all = args.all

    if not server_env or server_env not in ENVS:
        logger.error(f"A valid environment must be specified: {ENVS}")
        sys.exit(1)
    institutions = INSTITUTIONS[server_env]

    if not update_all and not update_ids:
        logger.error(
            "Nothing to update or create. Please either specify a list of institutions "
            "using --ids or run for all with --all"
        )
        sys.exit(1)
    elif update_all:
        institutions_to_update = institutions
    else:
        institutions_to_update = [
            inst for inst in institutions if inst["_id"] in update_ids
        ]
        diff_list = list(
            set(update_ids) - {inst["_id"] for inst in institutions_to_update}
        )
        if diff_list:
            logger.error(
                "One or more institution ID(s) provided via -i or --ids do not match any "
                "existing records: {}.".format(diff_list)
            )
            sys.exit(1)

    with transaction.atomic():
        for inst_data in institutions_to_update:
            update_or_create(inst_data)
        for extra_inst in Institution.objects.exclude(
            _id__in=[x["_id"] for x in institutions]
        ):
            logger.warning(
                f"Extra Institution : {extra_inst._id} - {extra_inst.name}"
            )


INSTITUTIONS = {
    "prod": [
        {
            "_id": "a2jlab",
            "name": "Access to Justice Lab",
            "description": 'Based within Harvard Law School, the <a href="https://a2jlab.org/">Access to Justice Lab</a> works with court administrators, legal service providers, and other stakeholders in the U.S. legal system to design and implement randomized field experiments evaluating interventions that impact access to justice.',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["a2jlab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "albion",
            "name": "Albion College",
            "description": 'This site is provided as a partnership between Albion College\'s Office of the President, the Carnegie Foundation for the Advancement of Teaching, and the U.S. National Advisory Committee for the Carnegie Elective Classification for Community Engagement. Projects must abide by <a href="https://web.albion.edu/student-life/information-technology/support/it-policies">Albion\'s Information Security Policies</a> | <a href="https://web.albion.edu/student-life/information-technology/about-it">Albion Information Technology</a>. Learn more about <a href="https://public-purpose.org/research/access-for-researchers/">the Public Purpose Institute and its commitment to data access</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("ethos01w.albion.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "asu",
            "name": "Arizona State University",
            "description": '<a href="https://asu.edu">Arizona State University</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:asu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.asu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "brown",
            "name": "Brown University",
            "description": 'A Research Project Management and Publication Tool for the Brown University Research Community in partnership with <a href="https://library.brown.edu/info/data_management">Brown University Library Research Data Management Services</a> | <a href="https://www.brown.edu/research/home">Research at Brown</a> | <a href="https://it.brown.edu/computing-policies/policy-handling-brown-restricted-information">Brown Restricted Information Handling Policy</a> | <a href="https://www.brown.edu/about/administration/provost/policies/privacy">Research Privacy Policy</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://sso.brown.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.brown.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "bt",
            "name": "Boys Town",
            "description": 'A research data service provided by the BTNRH Research Technology Core. Please do not use this service to store or transfer personally identifiable information or personal health information. For assistance please contact <a href="mailto:Christine.Hammans@boystown.org">Christine.Hammans@boystown.org</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://sts.windows.net/e2ab7419-36ab-4a95-a19f-ee90b6a9b8ac/"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://myapps.microsoft.com")
            ),
            "domains": ["osf.boystownhospital.org"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "bu",
            "name": "Boston University",
            "description": "A Research Project Management Tool for BU",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shib.bu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.bu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "busara",
            "name": "Busara Center for Behavioral Economics",
            "description": 'The <a href="http://www.busaracenter.org/">Busara Center</a> for Behavioral Economics',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["busaracenter.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "callutheran",
            "name": "California Lutheran University",
            "description": "",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("login.callutheran.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "capolicylab",
            "name": "California Policy Lab",
            "description": 'The <a href="https:www.capolicylab.org">California Policy Lab</a> pairs trusted experts from UCLA and UC Berkeley with policymakers to solve our most urgent social problems, including homelessness, poverty, crime, and education inequality.',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["capolicylab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "cfa",
            "name": "Center for Astrophysics | Harvard & Smithsonian",
            "description": 'Open Source Project Management Tools for the CfA Community: About <a href="https://cos.io/our-products/osf/">OSF</a> | <a href="https://www.cfa.harvard.edu/researchtopics">Research at the CfA</a> | <a href="https://library.cfa.harvard.edu/">CfA Library</a> | <a href="https://help.osf.io/">Get Help</a>',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["cfa.harvard.edu"],
            "delegation_protocol": "",
        },
        {
            "_id": "clrn",
            "name": "Character Lab Research Network",
            "description": ' Projects listed below are run through the <a href="https://www.characterlab.org/research-network">Character Lab Research Network</a>, a consortium of trailblazing schools and elite scientists that develop and test activities designed to help students thrive. Character Lab Research Network is a proud supporter of the Student Privacy Pledge to safeguard student privacy. For more details on the Research Network privacy policy, you can refer to the <a href="https://www.characterlab.org/student-privacy">Research Network student privacy policy</a> and <a href="https://www.characterlab.org/student-privacy/faqs">FAQs</a>.',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["characterlab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "cmu",
            "name": "Carnegie Mellon University",
            "description": 'A Project Management Tool for the CMU Community: <a href="https://l'
            'ibrary.cmu.edu/OSF">Get Help at CMU</a> | <a href="https://cos.io/o'
            'ur-products/osf/">About OSF</a> | <a href="https://help.osf.io/"'
            '>OSF Support</a> | <a href="https://library.cmu.edu/OSF/terms-of-us'
            'e">Terms of Use</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.cmu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.library.cmu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "colorado",
            "name": "University of Colorado Boulder",
            "description": 'This service is supported by the Center for Research Data and Digital Scholarship, which is led by <a href="https://www.rc.colorado.edu/">Research Computing</a> and the <a href="http://www.colorado.edu/libraries/">University Libraries</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://fedauth.colorado.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "cord",
            "name": "Concordia College",
            "description": '<a href="https://www.concordiacollege.edu/">Concordia College</a> | <a href="https://www.concordiacollege.edu/academics/library/">Carl B. Ylvisaker Library</a> | <a href="https://cord.libguides.com/?b=s">Research Guides</a>',
            "login_url": None,
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.cord.edu"],
            "email_domains": [],
            "delegation_protocol": "cas-pac4j",
        },
        {
            "_id": "cornell",
            "name": "Cornell University",
            "description": 'Supported by the Cornell Research Data Management Service Group and the Cornell University Library. The OSF service may not be used to store or transfer personally identifiable, confidential/restricted, HIPPA-regulated or any other controlled unclassified information. Learn more at <a href="https://data.research.cornell.edu">https://data.research.cornell.edu</a> | <a href="mailto:rdmsg-help@cornell.edu">rdmsg-help@cornell.edu</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shibidp.cit.cornell.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "cos",
            "name": "Center For Open Science",
            "description": 'COS is a non-profit technology company providing free and open services to increase inclusivity and transparency of research. Find out more at <a href="https://cos.io">cos.io</a>.',
            "login_url": None,
            "logout_url": None,
            "domains": ["osf.cos.io"],
            "email_domains": ["cos.io"],
            "delegation_protocol": "",
        },
        {
            "_id": "csic",
            "name": "Spanish National Research Council",
            "description": "Related resources are in the institutional intranet web site only.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://www.rediris.es/sir/csicidp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "cwru",
            "name": "Case Western Reserve University",
            "description": 'This site is provided as a partnership of the <a href="http://library.case.edu/ksl/">Kelvin Smith Library</a>, <a href="https://case.edu/utech/">University Technology</a>, and the <a href="https://case.edu/research/">Office of Research and Technology Management</a> at <a href="https://case.edu/">Case Western Reserve University</a>. Projects must abide by the <a href="https://case.edu/utech/departments/information-security/policies">University Information Security Policies</a> and <a href="https://case.edu/compliance/about/privacy-management/privacy-related-policies-cwru">Data Privacy Policies</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:case.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "duke",
            "name": "Duke University",
            "description": 'A research data service provided by <a href="https://library.duke.edu/data/data-management">Duke Libraries</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:duke.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ecu",
            "name": "East Carolina University",
            "description": 'In partnership with Academic Library Services and Laupus Health Sciences Library. Contact <a href="mailto:scholarlycomm@ecu.edu">scholarlycomm@ecu.edu</a> for more information. Researchers are individually responsible for abiding by university policies. ',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://sso.ecu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "esip",
            "name": "Federation of Earth Science Information Partners (ESIP)",
            "description": '<a href="http://www.esipfed.org/">ESIP\'s</a> mission is to support the networking and data dissemination needs of our members and the global Earth science data community by linking the functional sectors of observation, research, application, education and use of Earth science.',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["esipfed.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "eur",
            "name": "Erasmus University Rotterdam",
            "description": '<a href="https://doi.org/10.25397/eur.16912120.v1">EUR Data Policy</a> | '
            '<a href="https://my.eur.nl/en/eur-employee/work-support/cybersecurity/working-safely-it-eur">CyberSecurity at EUR</a> | '
            '<a href="https://my.eur.nl/en/eur-employee/work-support/cybersecurity/data-classification">EUR Data Classification</a> | '
            '<a href="https://my.eur.nl/en/eur-employee/research/research-services/research-data-management/rdm-policy/">EUR Data Classification (Examples)</a> | '
            '<a href="https://login.microsoftonline.com/715902d6-f63e-4b8d-929b-4bb170bad492/oauth2/authorize?client_id=00000003-0000-0ff1-ce00-000000000000&response_mode=form_post&protectedtoken=true&response_type=code%20id_token&resource=00000003-0000-0ff1-ce00-000000000000&scope=openid&nonce=65F9AF2BB43D7220657D949CB8FD3F4296DC77476CAACAF9-9161197C25231B477690A7A1C2BDFDF2BF0D6AA07DA0C6F3A8A9FBC3C5F0364F&redirect_uri=https%3A%2F%2Fliveeur.sharepoint.com%2F_forms%2Fdefault.aspx&state=OD0w&claims=%7B%22id_token%22%3A%7B%22xms_cc%22%3A%7B%22values%22%3A%5B%22CP1%22%5D%7D%7D%7D&wsucxt=1&cobrandid=11bd8083-87e0-41b5-bb78-0bc43c8a8e8a&client-request-id=d5792fa0-f064-3000-fabf-791a47aed3ce">EUR OSF Research Guidelines</a> | '
            '<a href="mailto:datasteward@eur.nl">Contact</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://sts.windows.net/715902d6-f63e-4b8d-929b-4bb170bad492/"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ferris",
            "name": "Ferris State University",
            "description": 'In partnership with the <a href="https://www.ferris.edu/research/">Office of Research and Sponsored Programs</a>, the <a href="https://www.ferris.edu/HTMLS/administration/academicaffairs/index.htm">Provost and Vice President for Academic Affairs</a>, and the <a href="https://www.ferris.edu/library/">FLITE Library</a>. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), intellectual property (IP) or any other controlled unclassified information (CUI). All projects must abide by the <a href="https://www.ferris.edu/HTMLS/administration/academicaffairs/Forms_Policies/Documents/Policy_Letters/AA-Intellectual-Property-Rights.pdf">FSU Intellectual Property Rights and Electronic Distance Learning Materials</a> letter of agreement.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("login.ferris.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "fsu",
            "name": "Florida State University",
            "description": 'This service is supported by the <a href="https://www.lib.fsu.edu/">FSU Libraries</a> for our research community. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), or any other controlled unclassified information (CUI). FSU\'s <a href="http://regulations.fsu.edu/sites/g/files/upcbnu486/files/policies/research/FSU%20Policy%207A-26.pdf">Research Data Management Policy</a> applies. For assistance please contact the FSU Libraries <a href="mailto:lib-datamgmt@fsu.edu">Research Data Management Program</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.fsu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.fsu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "gatech",
            "name": "Georgia Institute of Technology",
            "description": "This site is provided by the Georgia Tech Library.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.gatech.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "gmu",
            "name": "George Mason University",
            "description": 'This service is supported on campus by <a href="https://oria.gmu.edu/">Research Development, Integrity and Assurance</a> (RDIA), <a href="https://library.gmu.edu/"> The Office of Research Computing</a> (ORC), and <a href="https://orc.gmu.edu/">University Libraries</a>. Users should abide by all requirements of Mason\'s <a href="https://universitypolicy.gmu.edu/policies/data-stewardship/">Data Stewardship Policy</a> including not using this service to store or transfer highly sensitive data or any controlled unclassified information. For assistance please contact <a href="mailto:datahelp@gmu.edu">Wendy Mann</a>, Director of Mason\'s Digital Scholarship Center.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shibboleth.gmu.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "gwu",
            "name": "The George Washington University",
            "description": 'This service is supported by the <a href="https://library.gwu.edu/">GW Libraries</a> for our research community. Do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. Always abide by the <a href="https://compliance.gwu.edu/research-policies">GW Research Policies</a>. Contact the <a href="https://libguides.gwu.edu/prf.php?account_id=151788">GW Data Services Librarian</a> for support.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://singlesignon.gwu.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "harvard",
            "name": "Harvard University",
            "description": "This site is provided by Harvard Library.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://fed.huit.harvard.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ibhri",
            "name": "Integrative Behavioral Health Research Institute",
            "description": '<a href="https://www.ibhri.org/">The Integrative Behavioral Health Research Institute</a>',
            "login_url": None,
            "logout_url": None,
            "domains": ["osf.ibhri.org"],
            "email_domains": ["ibhri.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "icarehb",
            "name": "ICArEHB",
            "description": '<a href="https://www.icarehb.com">Interdisciplinary Center for Archaeology and Evolution of Human Behaviour</a>',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["icarehb.com"],
            "delegation_protocol": "",
        },
        {
            "_id": "icer",
            "name": "Institute for Clinical and Economic Review",
            "description": "",
            "login_url": None,
            "logout_url": None,
            "domains": ["osf.icer-review.org"],
            "email_domains": ["icer-review.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "igdore",
            "name": "Institute for Globally Distributed Open Research and Education (IGDORE)",
            "description": "Institute for Globally Distributed Open Research and Education "
            "(IGDORE) is an independent research institute dedicated to improve "
            "the quality of science, science education, and quality of life for "
            "scientists, students, and their families.",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["igdore.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "iit",
            "name": "Illinois Institute of Technology ",
            "description": "A research data service provided by Illinois Tech Libraries",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.iit.edu/cas/idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.iit.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "itb",
            "name": "Institut Teknologi Bandung",
            "description": "Institut Teknologi Bandung - OSF Repository",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.itb.ac.id/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "jhu",
            "name": "Johns Hopkins University",
            "description": 'A research data service provided by the <a href="https://www.library.jhu.edu/">Sheridan Libraries</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:johnshopkins.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.data.jhu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "jmu",
            "name": "James Madison University",
            "description": 'This service is supported on campus by the Office of Research and Scholarship, Central IT, and Libraries and Educational Technology for the JMU campus community. Do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. For assistance please contact the Library\'s Data Services Coordinator at <a href="mailto:shorisyl@jmu.edu">shorisyl@jmu.edu</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:jmu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.jmu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "jpal",
            "name": "J-PAL",
            "description": '<a href="https://www.povertyactionlab.org">https://www.povertyactionlab.org</a>',
            "login_url": None,
            "logout_url": None,
            "domains": ["osf.povertyactionlab.org"],
            "email_domains": ["povertyactionlab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "kuleuven",
            "name": "KU Leuven Libraries",
            "description": '<a href="https://bib.kuleuven.be/english/research">KU Leuven University Libraries</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "urn:mace:kuleuven.be:kulassoc:kuleuven.be"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ljaf",
            "name": "Laura and John Arnold Foundation",
            "description": 'Projects listed below are for grants awarded by the Foundation. Please see the <a href="http://www.arnoldfoundation.org/wp-content/uploads/Guidelines-for-Investments-in-Research.pdf">LJAF Guidelines for Investments in Research</a> for more information and requirements.',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["arnoldfoundation.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "mit",
            "name": "Massachusetts Institute of Technology",
            "description": 'A research data service provided by the <a href="https://libraries.mit.edu/">MIT Libraries</a>. Learn more about <a href="https://libraries.mit.edu/data-management/">MIT resources for data management</a>. Please abide by the Institution\'s policy on <a href="https://policies-procedures.mit.edu/privacy-and-disclosure-personal-information/protection-personal-privacy">Privacy and Disclosure of Information</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:mit.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "mq",
            "name": "Macquarie University",
            "description": 'In partnership with the Office of the Deputy Vice-Chancellor (Research) and the University Library. Learn more about <a href="https://staff.mq.edu.au/research/strategy-priorities-and-initiatives/data-science-and-eresearch">Data Science and eResearch</a> at Macquarie University.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "http://www.okta.com/exk2dzwun7KebsDIV2p7"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.mq.edu.au"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "nationalmaglab",
            "name": "National High Magnetic Field Laboratory",
            "description": 'This platform is provided to enable collaboration, sharing, and dissemination of research products from the National High Magnetic Field Laboratory according to the principles of <a href="https://www.go-fair.org/fair-principles/">FAIR</a> and open science. All public projects must adhere to <a href="https://nationalmaglab.org/about/policies-procedures">National MagLab policies & procedures</a> related to confidentiality and proper data management.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.fsu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "nesta",
            "name": "Nesta",
            "description": "<a href=\"https://www.nesta.org.uk/\">Nesta</a> is the UK's innovation agency for social good. We design, test and scale new solutions to society's biggest problems, changing millions of lives for the better.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("JumpCloud")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "nd",
            "name": "University of Notre Dame",
            "description": 'In <a href="https://research.nd.edu/news/64035-notre-dame-center-for-open-science-partner-to-advance-open-science-initiatives/">partnership</a> with the <a href="https://crc.nd.edu">Center for Research Computing</a>, <a href="http://esc.nd.edu">Engineering &amp; Science Computing</a>, and the <a href="https://library.nd.edu">Hesburgh Libraries</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.nd.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.nd.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "nyu",
            "name": "New York University",
            "description": 'A Research Project and File Management Tool for the NYU Community: <a href="https://www.nyu.edu/research.html">Research at NYU</a> | <a href="http://guides.nyu.edu/data_management">Research Data Management Planning</a> | <a href="https://library.nyu.edu/services/research/">NYU Library Research Services</a> | <a href="https://nyu.qualtrics.com/jfe6/form/SV_8dFc5TpA1FgLUMd">Get Help</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:nyu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component(
                    "https://shibboleth.nyu.edu/idp/profile/Logout"
                )
            ),
            "domains": ["osf.nyu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "okstate",
            "name": "Oklahoma State University",
            "description": '<a href="http://www.library.okstate.edu/research-support/research-data-services/">OSU Library Research Data Services</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://stwcas.okstate.edu/idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.library.okstate.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ou",
            "name": "The University of Oklahoma",
            "description": '<a href="https://www.ou.edu">The University of Oklahoma</a> | <a href="https://libraries.ou.edu">University Libraries</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shib.ou.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.ou.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "oxford",
            "name": "University of Oxford",
            "description": "",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "via-orcid",
            "orcid_record_verified_source": "ORCID Integration at the University of Oxford",
        },
        {
            "_id": "pu",
            "name": "Princeton University",
            "description": 'A research project management and sharing tool provided to the Princeton University research community by the <a href="https://library.princeton.edu/">Princeton University Library</a> and the <a href="https://researchdata.princeton.edu/">Princeton Research Data Service</a>. Projects must abide by University guidelines for <a href="https://ria.princeton.edu/research-data-security">Research Data Security and Privacy</a> and <a href="https://oit.princeton.edu/policies/information-security">Information Security</a> | <a href="https://github.com/CenterForOpenScience/cos.io/blob/master/TERMS_OF_USE.md">OSF Terms of Use</a> | <a href="https://github.com/CenterForOpenScience/cos.io/blob/master/PRIVACY_POLICY.md">OSF Privacy Policy</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://idp.princeton.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "purdue",
            "name": "Purdue University",
            "description": 'This open scholarship platform is provided by <a href="https://www.lib.purdue.edu/">Purdue University Libraries</a> in partnership with the University\'s <a href="https://www.purdue.edu/gradschool/">Graduate School</a>, <a href="https://www.purdue.edu/research/oevprp/regulatory-affairs/">Regulatory Affairs</a>, and <a href="https://www.purdue.edu/provost/researchIntegrity/">Research Integrity Office</a>.<br><br>All projects must adhere to Purdue\'s <a href="https://www.purdue.edu/policies/information-technology/viib8.html#statement">Information security</a>, <a href="https://www.purdue.edu/policies/academic-research-affairs/ic1.html">Human subjects research</a> policies, and related <a href="https://www.purdue.edu/securepurdue/data-handling/index.php">data classification and handling procedures</a>. Associated guidance on regulations is available via the <a href="https://www.purdue.edu/research/oevprp/regulatory-affairs/responsible-conduct.php">Responsible Conductof Research website</a> and the <a href="https://www.purdue.edu/provost/researchIntegrity/">Research Integrity Office</a>. For questions and support please reach out to <a href="mailto:riboehm@purdue.edu">Purdue\'s OSF contact</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.purdue.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "sc",
            "name": "University of South Carolina Libraries",
            "description": 'Brought to you by <a href="http://library.sc.edu/">University Libraries</a> at the University of South Carolina.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://cas.auth.sc.edu/cas/idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.sc.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "temple",
            "name": "Temple University",
            "description": 'Projects must abide by Temple University\'s <a href="https://www.temple.edu/privacy-statement">Privacy Statement</a>, <a href="https://its.temple.edu/technology-usage-policy">Technology Usage Policy</a>, <a href="https://its.temple.edu/classification-and-handling-protected-data">University Classification and Handling of Protected Data</a>, and <a href="https://its.temple.edu/guidelines-storing-and-using-personally-identifiable-information-non-production-environments">Guidelines for Storing and Using Personally Identifiable Information in Non-Production Environments</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://fim.temple.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "thepolicylab",
            "name": "The Policy Lab at Brown University",
            "description": 'The Policy Lab at Brown University conducts applied research to improve public policy in Rhode Island and beyond.<br />Learn more at <a href="https://thepolicylab.brown.edu/">thepolicylab.brown.edu</a> and tune into our podcast, <a href="https://thirtythousandleagues.com/">30,000 Leagues</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://sso.brown.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "thelabatdc",
            "name": "The Lab @ DC",
            "description": 'The Lab @ DC is an entity of the <a href="https://mayor.dc.gov/">Executive Office of the Mayor of the District of Columbia Government</a>. We work in the <a href="https://oca.dc.gov/">Office of the City Administrator</a> and in partnership with a network of universities and research centers to apply the scientific method into day-to-day governance.',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["dc.gov"],
            "delegation_protocol": "",
        },
        {
            "_id": "theworks",
            "name": "The Works Research Institute",
            "description": "The Works Research Institute",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["theworks.info"],
            "delegation_protocol": "",
        },
        {
            "_id": "tufts",
            "name": "Tufts University",
            "description": '<a href="http://researchguides.library.tufts.edu/RDM">Research Data Management &#64; Tufts</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shib-idp.tufts.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ua",
            "name": "University of Arizona",
            "description": 'A service supported by the <a href="http://www.library.arizona.edu/">University of Arizona Libraries</a>. For more information, please refer to the <a href="http://data.library.arizona.edu/osf">UA Data Management Page</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:arizona.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.arizona.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ubc",
            "name": "University of British Columbia",
            "description": 'Users are reminded to ensure their use of this service is in compliance with all <a href="https://universitycounsel.ubc.ca/policies/">UBC Policies and Standards</a>. Please refer specifically to <a href="https://universitycounsel.ubc.ca/files/2015/08/policy85.pdf">Policy 85</a>, <a href="https://universitycounsel.ubc.ca/files/2013/06/policy104.pdf">Policy 104</a>, and the <a href="https://cio.ubc.ca/node/1073">Information Security Standards</a>. Find out more about <a href="http://openscience.ubc.ca">OSF</a>. Get help with <a href="https://researchdata.library.ubc.ca/">Research Data Management</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://authentication.ubc.ca")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.openscience.ubc.ca"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uc",
            "name": "University of Cincinnati",
            "description": 'In partnership with the <a href="https://research.uc.edu/home/officeofresearch/administrativeoffices.aspx">Office of Research</a>, <a href="https://www.libraries.uc.edu/">UC Libraries</a> and <a href="https://www.uc.edu/ucit.html">IT&#64;UC</a>. Projects must abide by <a href="http://www.uc.edu/infosec/policies.html">Security (9.1.27) and Data Protection (9.1.1) Policies.</a> Learn more by visiting <a href="https://libraries.uc.edu/digital-scholarship/data-services.html">Research Data & GIS services</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.uc.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.uc.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ucla",
            "name": "UCLA",
            "description": 'A research data service provided by the <a href="https://www.library.ucla.edu/">UCLA Library</a>. Please do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. For assistance please contact <a href="mailto:data@library.ucla.edu">data@library.ucla.edu</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:ucla.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.ucla.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ucsd",
            "name": "University of California San Diego",
            "description": 'This service is supported on campus by the UC San Diego Library for our research community. Do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. For assistance please contact the Library\'s Research Data Curation Program at <a href="mailto:research-data-curation@ucsd.edu">research-data-curation@ucsd.edu</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:ucsd.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.ucsd.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ucr",
            "name": "University of California Riverside",
            "description": 'Policy prohibits storing PII or HIPAA data on this site, please see C&amp;C\'s <a href="http://cnc.ucr.edu/security/researchers.html">security site</a> for more information.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:ucr.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.ucr.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uct",
            "name": "University of Cape Town",
            "description": '<a href="http://www.lib.uct.ac.za/">UCT Libraries</a>, <a href="http://www.eresearch.uct.ac.za/">UCT eResearch</a> &amp; <a href="http://www.icts.uct.ac.za/">ICTS</a> present the UCT OSF institutional service to UCT affiliated students, staff and researchers. The UCT OSF facility should be used in conjunction with the institution\'s <a href="http://www.digitalservices.lib.uct.ac.za/dls/rdm-policy">Research Data Management (RDM) Policy</a>, <a href="https://www.uct.ac.za/downloads/uct.ac.za/about/policies/UCTOpenAccessPolicy.pdf">Open Access Policy</a> and <a href="https://www.uct.ac.za/downloads/uct.ac.za/about/policies/UCTOpenAccessPolicy.pdf">IP Policy</a>. Visit the <a href="http://www.digitalservices.lib.uct.ac.za/">UCT Digital Library Services</a> for more information and/or assistance with <a href="http://www.digitalservices.lib.uct.ac.za/dls/rdm">RDM</a> and <a href="http://www.digitalservices.lib.uct.ac.za/dls/data-sharing-guidelines">data sharing</a>. We also encourage the use of UCT Libraries\'s Data Management Planning tool, <a href="http://dmp.lib.uct.ac.za/about_us">DMPonline</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "http://adfs.uct.ac.za/adfs/services/trust"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.uct.ac.za"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ugent",
            "name": "Universiteit Gent",
            "description": None,
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://identity.ugent.be/simplesaml/saml2/idp/metadata.php"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.ugent.be"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ugoe",
            "name": "University of Göttingen",
            "description": 'In partnership with <a href="https://www.sub.uni-goettingen.de/">Göttingen State and University Library</a>, the <a href="http://www.eresearch.uni-goettingen.de/">Göttingen eResearch Alliance</a> and the <a href="https://www.gwdg.de/">Gesellschaft für wissenschaftliche Datenverarbeitung Göttingen</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shibboleth-idp.uni-goettingen.de/uni/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.uni-goettingen.de"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "umb",
            "name": "University of Maryland, Baltimore",
            "description": 'This research data management service is supported by the <a href="https://www2.hshsl.umaryland.edu/cdabs/">Center for Data and Bioinformtion Services</a> at the <a href="https://www.hshsl.umaryland.edu/">Health Sciences and Human Services Library</a>. This platform is not intended for the storage of PII or PHI.<br><a href="https://www.umaryland.edu/policies-and-procedures/library/research/policies/iv-9901a.php">UMB Policy Regarding Ownership, Management, and Sharing of Research Data</a> | For questions contact <a href="mailto:data@hshsl.umaryland.edu">data@hshsl.umaryland.edu</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://webauth.umaryland.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "umd",
            "name": "University of Maryland",
            "description": "University of Maryland",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:umd.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "unc",
            "name": "University of North Carolina at Chapel Hill",
            "description": 'This service is supported by <a href="https://odum.unc.edu/">The Odum Institute for Research in Social Science</a> and <a href="https://library.unc.edu">University Libraries at the University of North Carolina at Chapel Hill</a>. Please do not store or transfer personally identifiable information, personal health information, or any other sensitive or proprietary data in the OSF. Projects should follow applicable <a href="https://unc.policystat.com/">UNC policies</a>. Contact the <a href="mailto:odumarchive@unc.edu">Odum Institute Data Archive</a> with any questions.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:unc.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "universityofkent",
            "name": "University of Kent",
            "description": 'Collaboration Platform for University of Kent Research | <a href="https://www.kent.ac.uk/governance/policies-and-procedures/documents/Information-security-policy-v1-1.pdf">Information Security policy</a> | <a href="mailto:researchsupport@kent.ac.uk">Help and Support</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://sso.id.kent.ac.uk/idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uol",
            "name": "University of London",
            "description": "A research project management and publication platform for the University of London research community",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://idp.uolia.london.ac.uk/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uom",
            "name": "University of Manchester",
            "description": 'OSF is currently only supported for FBMH Core Facility users, for further information contact <a href="mailto:danielle.owen@manchester.ac.uk">danielle.owen@manchester.ac.uk</a>. <a href="https://www.manchester.ac.uk/discover/privacy-information/">University of Manchester Privacy Policy</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shib.manchester.ac.uk/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "usc",
            "name": "University of Southern California",
            "description": 'Projects must abide by <a href="http://policy.usc.edu/info-security/">USC\'s Information Security Policy</a>. Data stored for human subject research repositories must abide by <a href="http://policy.usc.edu/biorepositories/">USC\'s Biorepository Policy</a>. The OSF may not be used for storage of Personal Health Information that is subject to <a href="http://policy.usc.edu/hipaa/">HIPPA regulations</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:usc.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.usc.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ush",
            "name": "Universal Sustainability Hub",
            "description": '<a href="https://uvers.ac.id/">Universal Sustainability Hub for Universal Family</a>',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["uvers.ac.id"],
            "delegation_protocol": "",
        },
        {
            "_id": "utdallas",
            "name": "The University of Texas at Dallas",
            "description": 'In partnership with the Office of Research. Learn more about <a href="https://data.utdallas.edu/">UT Dallas resources for computational and data-driven research</a>. Projects must abide by university security and data protection policies.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.utdallas.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.utdallas.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uva",
            "name": "University of Virginia",
            "description": 'In partnership with the <a href="http://www.virginia.edu/vpr/">Vice President for Research</a>, <a href="http://dsi.virginia.edu">Data Science Institute</a>, <a href="https://www.hsl.virginia.edu">Health Sciences Library</a>, and <a href="http://data.library.virginia.edu">University Library</a>. Learn more about <a href="http://cadre.virginia.edu">UVA resources for computational and data-driven research</a>. Projects must abide by the <a href="http://www.virginia.edu/informationpolicy/security.html">University Security and Data Protection Policies</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:virginia.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.virginia.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uw",
            "name": "University of Washington",
            "description": 'This service is supported by the University of Washington Libraries. Do not use this service to store or transfer personally identifiable information or personal health information. Questions? Email the Libraries Research Data Services Unit at <a href="mailto:libdata@uw.edu">libdata@uw.edu</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:washington.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uwstout",
            "name": "University of Wisconsin - Stout",
            "description": 'A Research Project and File Management Tool for the UW-Stout Community: <a href="https://wwwcs.uwstout.edu/rs/index.cfm">Office of Research and Sponsored Programs</a> | <a href="https://wwwcs.uwstout.edu/lib/">University Library</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://smidp.uwstout.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["open.uwstout.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "vcu",
            "name": "Virginia Commonwealth University",
            "description": 'This service is supported by the VCU Libraries and the VCU Office of Research and Innovation for our research community. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), or any other controlled unclassified information (CUI). VCU\'s policy entitled "<a href="http://www.policy.vcu.edu/sites/default/files/Research%20Data%20Ownership,%20Retention,%20Access%20and%20Securty.pdf">Research Data Ownership, Retention, Access and Security</a>" applies. For assistance please contact the <a href="https://www.library.vcu.edu/services/data/">VCU Libraries Research Data Management Program</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shibboleth.vcu.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.research.vcu.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "vt",
            "name": "Virginia Tech",
            "description": 'Made possible by the <a href="https://www.lib.vt.edu">University Libraries</a> in partnership with <a href="https://secure.hosting.vt.edu/www.arc.vt.edu/">Advanced Research Computing</a> and the <a href="https://research.vt.edu/">Office of the Vice President for Research</a>. Using the Virginia Tech login to OSF provides your name and VT email address to the Center for Open Science. Please see their <a href="https://github.com/CenterForOpenScience/cos.io/blob/master/TERMS_OF_USE.md">terms of service</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:vt.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "vua",
            "name": "Vrije Universiteit Amsterdam",
            "description": 'A Research Data Management Tool for the Vrije Universiteit Amsterdam Research Community. <a href="https://osf.io/abwzm/wiki/home/">VU OSF Getting Started Guide</a> | <a href="https://vu.nl/en/employee/research-data-support">VU Research Data Support</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "http://stsfed.login.vu.nl/adfs/services/trust"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.vu.nl"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "wustl",
            "name": "Washington University in St. Louis",
            "description": 'This service is supported by the <a href="https://library.wustl.edu">Washington University in St. Louis Libraries</a>. Please abide by the University policy on <a href="https://informationsecurity.wustl.edu/resources/information-security-solutions/data-classification/">information security</a>. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), or any other controlled unclassified information (CUI). | For assistance please contact the <a href="http://gis.wustl.edu/dgs">WU Libraries Data & GIS Services</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.wustl.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://osf.io/goodbye")
            ),
            "domains": ["osf.wustl.edu"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
    ],
    "stage": [
        {
            "_id": "cos",
            "name": "Center For Open Science [Stage]",
            "description": "Center for Open Science [Stage]",
            "login_url": None,
            "logout_url": None,
            "domains": ["staging-osf.cos.io"],
            "email_domains": ["cos.io"],
            "delegation_protocol": "",
        },
        {
            "_id": "nd",
            "name": "University of Notre Dame [Stage]",
            "description": "University of Notre Dame [Stage]",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://login-test.cc.nd.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://staging.osf.io/goodbye")
            ),
            "domains": ["staging-osf-nd.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "google",
            "name": "Google [Stage]",
            "description": "Google [Stage]",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["gmail.com"],
            "delegation_protocol": "",
        },
        {
            "_id": "yahoo",
            "name": "Yahoo [Stage]",
            "description": "Yahoo [Stage]",
            "login_url": None,
            "domains": [],
            "email_domains": ["yahoo.com"],
            "delegation_protocol": "",
        },
        {
            "_id": "oxford",
            "name": "University of Oxford [Stage]",
            "description": "Here is the place to put in links to other resources, security and data policies, research guidelines, and/or a contact for user support within your institution.",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "via-orcid",
            "orcid_record_verified_source": "ORCID Integration at the University of Oxford",
        },
        {
            "_id": "osftype1",
            "name": 'Fake "via-ORCiD" Institution [Stage]',
            "description": "Fake OSF Institution Type 1. This institution uses ORCiD SSO for login and its user "
            "affiliation is retrieved from ORCiD public record.",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "via-orcid",
            "orcid_record_verified_source": "OSF Integration",
        },
    ],
    "stage2": [
        {
            "_id": "cos",
            "name": "Center For Open Science [Stage2]",
            "description": "Center for Open Science [Stage2]",
            "login_url": None,
            "logout_url": None,
            "domains": ["staging2-osf.cos.io"],
            "email_domains": ["cos.io"],
            "delegation_protocol": "",
        },
    ],
    "stage3": [
        {
            "_id": "cos",
            "name": "Center For Open Science [Stage3]",
            "description": "Center for Open Science [Stage3]",
            "login_url": None,
            "logout_url": None,
            "domains": ["staging3-osf.cos.io"],
            "email_domains": ["cos.io"],
            "delegation_protocol": "",
        },
    ],
    "test": [
        {
            "_id": "osfidemo",
            "name": "OSF Demo Institution",
            "description": "Here is the place to put in links to other resources, security and data policies, research guidelines, and/or a contact for user support within your institution.",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "",
        },
        {
            "_id": "a2jlab",
            "name": "Access to Justice Lab [Test]",
            "description": 'Based within Harvard Law School, the <a href="https://a2jlab.org/">Access to Justice Lab</a> works with court administrators, legal service providers, and other stakeholders in the U.S. legal system to design and implement randomized field experiments evaluating interventions that impact access to justice.',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["a2jlab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "albion",
            "name": "Albion College [Test]",
            "description": 'This site is provided as a partnership between Albion College\'s Office of the President, the Carnegie Foundation for the Advancement of Teaching, and the U.S. National Advisory Committee for the Carnegie Elective Classification for Community Engagement. Projects must abide by <a href="https://web.albion.edu/student-life/information-technology/support/it-policies">Albion\'s Information Security Policies</a> | <a href="https://web.albion.edu/student-life/information-technology/about-it">Albion Information Technology</a>. Learn more about <a href="https://public-purpose.org/research/access-for-researchers/">the Public Purpose Institute and its commitment to data access</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("ethos01w.albion.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ablbion.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "asu",
            "name": "Arizona State University [Test]",
            "description": '<a href="https://asu.edu">Arizona State University</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:asu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-asu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "brown",
            "name": "Brown University [Test]",
            "description": 'A Research Project Management and Publication Tool for the Brown University Research Community in partnership with <a href="https://library.brown.edu/info/data_management">Brown University Library Research Data Management Services</a> | <a href="https://www.brown.edu/research/home">Research at Brown</a> | <a href="https://it.brown.edu/computing-policies/policy-handling-brown-restricted-information">Brown Restricted Information Handling Policy</a> | <a href="https://www.brown.edu/about/administration/provost/policies/privacy">Research Privacy Policy</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://sso.brown.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-brown.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "bt",
            "name": "Boys Town [Test]",
            "description": 'A research data service provided by the BTNRH Research Technology Core. Please do not use this service to store or transfer personally identifiable information or personal health information. For assistance please contact <a href="mailto:Christine.Hammans@boystown.org">Christine.Hammans@boystown.org</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://sts.windows.net/e2ab7419-36ab-4a95-a19f-ee90b6a9b8ac/"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://myapps.microsoft.com")
            ),
            "domains": ["test-osf-bt.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "bu",
            "name": "Boston University [Test]",
            "description": "A Research Project Management Tool for BU",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shib.bu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-bu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "busara",
            "name": "Busara Center for Behavioral Economics [Test]",
            "description": 'The <a href="http://www.busaracenter.org/">Busara Center</a> for Behavioral Economics',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["busaracenter.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "callutheran",
            "name": "California Lutheran University SAML-SSO [Test]",
            "description": "",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("login.callutheran.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-callutheran.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "callutheran2",
            "name": "California Lutheran University CAS-SSO [Test]",
            "description": "",
            "login_url": None,
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-callutheran2.cos.io"],
            "email_domains": [],
            "delegation_protocol": "cas-pac4j",
        },
        {
            "_id": "capolicylab",
            "name": "California Policy Lab [Test]",
            "description": 'The <a href="https:www.capolicylab.org">California Policy Lab</a> pairs trusted experts from UCLA and UC Berkeley with policymakers to solve our most urgent social problems, including homelessness, poverty, crime, and education inequality.',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["capolicylab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "cfa",
            "name": "Center for Astrophysics | Harvard & Smithsonian [Test]",
            "description": 'Open Source Project Management Tools for the CfA Community: About <a href="https://cos.io/our-products/osf/">OSF</a> | <a href="https://www.cfa.harvard.edu/researchtopics">Research at the CfA</a> | <a href="https://library.cfa.harvard.edu/">CfA Library</a> | <a href="https://help.osf.io/">Get Help</a>',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["cfa.harvard.edu"],
            "delegation_protocol": "",
        },
        {
            "_id": "clrn",
            "name": "Character Lab Research Network [Test]",
            "description": ' Projects listed below are run through the <a href="https://www.characterlab.org/research-network">Character Lab Research Network</a>, a consortium of trailblazing schools and elite scientists that develop and test activities designed to help students thrive. Character Lab Research Network is a proud supporter of the Student Privacy Pledge to safeguard student privacy. For more details on the Research Network privacy policy, you can refer to the <a href="https://www.characterlab.org/student-privacy">Research Network student privacy policy</a> and <a href="https://www.characterlab.org/student-privacy/faqs">FAQs</a>.',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["characterlab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "cmu",
            "name": "Carnegie Mellon University [Test]",
            "description": 'A Project Management Tool for the CMU Community: <a href="https://l'
            'ibrary.cmu.edu/OSF">Get Help at CMU</a> | <a href="https://cos.io/o'
            'ur-products/osf/">About OSF</a> | <a href="https://help.osf.io/"'
            '>OSF Support</a> | <a href="https://library.cmu.edu/OSF/terms-of-us'
            'e">Terms of Use</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.cmu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-cmu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "colorado",
            "name": "University of Colorado Boulder [Test]",
            "description": 'This service is supported by the Center for Research Data and Digital Scholarship, which is led by <a href="https://www.rc.colorado.edu/">Research Computing</a> and the <a href="http://www.colorado.edu/libraries/">University Libraries</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://fedauth.colorado.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "cornell",
            "name": "Cornell University [Test]",
            "description": 'Supported by the Cornell Research Data Management Service Group and the Cornell University Library. The OSF service may not be used to store or transfer personally identifiable, confidential/restricted, HIPPA-regulated or any other controlled unclassified information. Learn more at <a href="https://data.research.cornell.edu">https://data.research.cornell.edu</a> | <a href="mailto:rdmsg-help@cornell.edu">rdmsg-help@cornell.edu</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shibidp.cit.cornell.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-cornell.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "cord",
            "name": "Concordia College [Test]",
            "description": '<a href="https://www.concordiacollege.edu/">Concordia College</a> | <a href="https://www.concordiacollege.edu/academics/library/">Carl B. Ylvisaker Library</a> | <a href="https://cord.libguides.com/?b=s">Research Guides</a>',
            "login_url": None,
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-cord.cos.io"],
            "email_domains": [],
            "delegation_protocol": "cas-pac4j",
        },
        {
            "_id": "cos",
            "name": "Center For Open Science [Test]",
            "description": 'COS is a non-profit technology company providing free and open services to increase inclusivity and transparency of research. Find out more at <a href="https://cos.io">cos.io</a>.',
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf.cos.io"],
            "email_domains": ["cos.io"],
            "delegation_protocol": "",
        },
        {
            "_id": "csic",
            "name": "Spanish National Research Council [Test]",
            "description": "Related resources are in the institutional intranet web site only.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://www.rediris.es/sir/shibtestidp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "cwru",
            "name": "Case Western Reserve University [Test]",
            "description": 'This site is provided as a partnership of the <a href="http://library.case.edu/ksl/">Kelvin Smith Library</a>, <a href="https://case.edu/utech/">University Technology</a>, and the <a href="https://case.edu/research/">Office of Research and Technology Management</a> at <a href="https://case.edu/">Case Western Reserve University</a>. Projects must abide by the <a href="https://case.edu/utech/departments/information-security/policies">University Information Security Policies</a> and <a href="https://case.edu/compliance/about/privacy-management/privacy-related-policies-cwru">Data Privacy Policies</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:case.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-cwru.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "duke",
            "name": "Duke University [Test]",
            "description": 'A research data service provided by <a href="https://library.duke.edu/data/data-management">Duke Libraries</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:duke.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ecu",
            "name": "East Carolina University [Test]",
            "description": 'In partnership with Academic Library Services and Laupus Health Sciences Library. Contact <a href="mailto:scholarlycomm@ecu.edu">scholarlycomm@ecu.edu</a> for more information. Researchers are individually responsible for abiding by university policies. ',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://sso.ecu.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "esip",
            "name": "Federation of Earth Science Information Partners (ESIP) [Test]",
            "description": '<a href="http://www.esipfed.org/">ESIP\'s</a> mission is to support the networking and data dissemination needs of our members and the global Earth science data community by linking the functional sectors of observation, research, application, education and use of Earth science.',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["esipfed.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "eur",
            "name": "Erasmus University Rotterdam [Test]",
            "description": '<a href="https://doi.org/10.25397/eur.16912120.v1">EUR Data Policy</a> | '
            '<a href="https://my.eur.nl/en/eur-employee/work-support/cybersecurity/working-safely-it-eur">CyberSecurity at EUR</a> | '
            '<a href="https://my.eur.nl/en/eur-employee/work-support/cybersecurity/data-classification">EUR Data Classification</a> | '
            '<a href="https://my.eur.nl/en/eur-employee/research/research-services/research-data-management/rdm-policy/">EUR Data Classification (Examples)</a> | '
            '<a href="https://login.microsoftonline.com/715902d6-f63e-4b8d-929b-4bb170bad492/oauth2/authorize?client_id=00000003-0000-0ff1-ce00-000000000000&response_mode=form_post&protectedtoken=true&response_type=code%20id_token&resource=00000003-0000-0ff1-ce00-000000000000&scope=openid&nonce=65F9AF2BB43D7220657D949CB8FD3F4296DC77476CAACAF9-9161197C25231B477690A7A1C2BDFDF2BF0D6AA07DA0C6F3A8A9FBC3C5F0364F&redirect_uri=https%3A%2F%2Fliveeur.sharepoint.com%2F_forms%2Fdefault.aspx&state=OD0w&claims=%7B%22id_token%22%3A%7B%22xms_cc%22%3A%7B%22values%22%3A%5B%22CP1%22%5D%7D%7D%7D&wsucxt=1&cobrandid=11bd8083-87e0-41b5-bb78-0bc43c8a8e8a&client-request-id=d5792fa0-f064-3000-fabf-791a47aed3ce">EUR OSF Research Guidelines</a> | '
            '<a href="mailto:datasteward@eur.nl">Contact</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://sts.windows.net/715902d6-f63e-4b8d-929b-4bb170bad492/"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ferris",
            "name": "Ferris State University [Test]",
            "description": 'In partnership with the <a href="https://www.ferris.edu/research/">Office of Research and Sponsored Programs</a>, the <a href="https://www.ferris.edu/HTMLS/administration/academicaffairs/index.htm">Provost and Vice President for Academic Affairs</a>, and the <a href="https://www.ferris.edu/library/">FLITE Library</a>. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), intellectual property (IP) or any other controlled unclassified information (CUI). All projects must abide by the <a href="https://www.ferris.edu/HTMLS/administration/academicaffairs/Forms_Policies/Documents/Policy_Letters/AA-Intellectual-Property-Rights.pdf">FSU Intellectual Property Rights and Electronic Distance Learning Materials</a> letter of agreement.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("login.ferris.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "fsu",
            "name": "Florida State University [Test]",
            "description": 'This service is supported by the <a href="https://www.lib.fsu.edu/">FSU Libraries</a> for our research community. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), or any other controlled unclassified information (CUI). FSU\'s <a href="http://regulations.fsu.edu/sites/g/files/upcbnu486/files/policies/research/FSU%20Policy%207A-26.pdf">Research Data Management Policy</a> applies. For assistance please contact the FSU Libraries <a href="mailto:lib-datamgmt@fsu.edu">Research Data Management Program</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.fsu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-fsu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "gatech",
            "name": "Georgia Institute of Technology [Test]",
            "description": "This site is provided by the Georgia Tech Library.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.gatech.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "gmu",
            "name": "George Mason University [Test]",
            "description": 'This service is supported on campus by <a href="https://oria.gmu.edu/">Research Development, Integrity and Assurance</a> (RDIA), <a href="https://library.gmu.edu/"> The Office of Research Computing</a> (ORC), and <a href="https://orc.gmu.edu/">University Libraries</a>. Users should abide by all requirements of Mason\'s <a href="https://universitypolicy.gmu.edu/policies/data-stewardship/">Data Stewardship Policy</a> including not using this service to store or transfer highly sensitive data or any controlled unclassified information. For assistance please contact <a href="mailto:datahelp@gmu.edu">Wendy Mann</a>, Director of Mason\'s Digital Scholarship Center.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shibboleth.gmu.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-gmu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "gwu",
            "name": "The George Washington University [Test]",
            "description": 'This service is supported by the <a href="https://library.gwu.edu/">GW Libraries</a> for our research community. Do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. Always abide by the <a href="https://compliance.gwu.edu/research-policies">GW Research Policies</a>. Contact the <a href="https://libguides.gwu.edu/prf.php?account_id=151788">GW Data Services Librarian</a> for support.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://singlesignon.gwu.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-gwu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "harvard",
            "name": "Harvard University [Test]",
            "description": "This site is provided by Harvard Library.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://fed.huit.harvard.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-harvard.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ibhri",
            "name": "Integrative Behavioral Health Research Institute [Test]",
            "description": '<a href="https://www.ibhri.org/">The Integrative Behavioral Health Research Institute</a>',
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf-ibhri.cos.io"],
            "email_domains": ["ibhri.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "icarehb",
            "name": "ICArEHB [Test]",
            "description": '<a href="https://www.icarehb.com">Interdisciplinary Center for Archaeology and Evolution of Human Behaviour</a>',
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf-icarehb.cos.io"],
            "email_domains": ["icarehb.com"],
            "delegation_protocol": "",
        },
        {
            "_id": "icer",
            "name": "Institute for Clinical and Economic Review [Test]",
            "description": "",
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf-icer.cos.io"],
            "email_domains": ["icer-review.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "igdore",
            "name": "Institute for Globally Distributed Open Research and Education [Test]",
            "description": "Institute for Globally Distributed Open Research and Education "
            "(IGDORE) is an independent research institute dedicated to improve "
            "the quality of science, science education, and quality of life for "
            "scientists, students, and their families.",
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf-icer.igdore.io"],
            "email_domains": ["igdore.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "iit",
            "name": "Illinois Institute of Technology [Test]",
            "description": "A research data service provided by Illinois Tech Libraries",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.iit.edu/cas/idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-iit.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "itb",
            "name": "Institut Teknologi Bandung [Test]",
            "description": "Institut Teknologi Bandung - OSF Repository",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://login-dev3.itb.ac.id/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-itb.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "jhu",
            "name": "Johns Hopkins University [Test]",
            "description": 'A research data service provided by the <a href="https://www.library.jhu.edu/">Sheridan Libraries</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:johnshopkins.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-jhu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "jmu",
            "name": "James Madison University [Test]",
            "description": 'This service is supported on campus by the Office of Research and Scholarship, Central IT, and Libraries and Educational Technology for the JMU campus community. Do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. For assistance please contact the Library\'s Data Services Coordinator at <a href="mailto:shorisyl@jmu.edu">shorisyl@jmu.edu</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:jmu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-jmu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "jpal",
            "name": "J-PAL [Test]",
            "description": '<a href="https://www.povertyactionlab.org">https://www.povertyactionlab.org</a>',
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf-jpal.cos.io"],
            "email_domains": ["povertyactionlab.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "kuleuven",
            "name": "KU Leuven Libraries [Test]",
            "description": '<a href="https://bib.kuleuven.be/english/research">KU Leuven University Libraries</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "urn:mace:kuleuven.be:kulassoc:kuleuven.be"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ljaf",
            "name": "Laura and John Arnold Foundation [Test]",
            "description": 'Projects listed below are for grants awarded by the Foundation. Please see the <a href="http://www.arnoldfoundation.org/wp-content/uploads/Guidelines-for-Investments-in-Research.pdf">LJAF Guidelines for Investments in Research</a> for more information and requirements.',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["arnoldfoundation.org"],
            "delegation_protocol": "",
        },
        {
            "_id": "mit",
            "name": "Massachusetts Institute of Technology [Test]",
            "description": 'A research data service provided by the <a href="https://libraries.mit.edu/">MIT Libraries</a>. Learn more about <a href="https://libraries.mit.edu/data-management/">MIT resources for data management</a>. Please abide by the Institution\'s policy on <a href="https://policies-procedures.mit.edu/privacy-and-disclosure-personal-information/protection-personal-privacy">Privacy and Disclosure of Information</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:mit.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-mit.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "mq",
            "name": "Macquarie University [Test]",
            "description": 'In partnership with the Office of the Deputy Vice-Chancellor (Research) and the University Library. Learn more about <a href="https://staff.mq.edu.au/research/strategy-priorities-and-initiatives/data-science-and-eresearch">Data Science and eResearch</a> at Macquarie University.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "http://www.okta.com/exkebok0cpJxGzMKz0h7"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-mq.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "nationalmaglab",
            "name": "National High Magnetic Field Laboratory [Test]",
            "description": 'This platform is provided to enable collaboration, sharing, and dissemination of research products from the National High Magnetic Field Laboratory according to the principles of <a href="https://www.go-fair.org/fair-principles/">FAIR</a> and open science. All public projects must adhere to <a href="https://nationalmaglab.org/about/policies-procedures">National MagLab policies & procedures</a> related to confidentiality and proper data management.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.fsu.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-nationalmaglab.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "nesta",
            "name": "Nesta [Test]",
            "description": "<a href=\"https://www.nesta.org.uk/\">Nesta</a> is the UK's innovation agency for social good. We design, test and scale new solutions to society's biggest problems, changing millions of lives for the better.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("JumpCloud")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "nd",
            "name": "University of Notre Dame [Test]",
            "description": 'In <a href="https://research.nd.edu/news/64035-notre-dame-center-for-open-science-partner-to-advance-open-science-initiatives/">partnership</a> with the <a href="https://crc.nd.edu">Center for Research Computing</a>, <a href="http://esc.nd.edu">Engineering &amp; Science Computing</a>, and the <a href="https://library.nd.edu">Hesburgh Libraries</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://login-test.cc.nd.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-nd.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "nyu",
            "name": "New York University [Test]",
            "description": 'A Research Project and File Management Tool for the NYU Community: <a href="https://www.nyu.edu/research.html">Research at NYU</a> | <a href="http://guides.nyu.edu/data_management">Research Data Management Planning</a> | <a href="https://library.nyu.edu/services/research/">NYU Library Research Services</a> | <a href="https://nyu.qualtrics.com/jfe6/form/SV_8dFc5TpA1FgLUMd">Get Help</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shibbolethqa.es.its.nyu.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component(
                    "https://shibbolethqa.es.its.nyu.edu/idp/profile/Logout"
                )
            ),
            "domains": ["test-osf-nyu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "okstate",
            "name": "Oklahoma State University [Test]",
            "description": '<a href="http://www.library.okstate.edu/research-support/research-data-services/">OSU Library Research Data Services</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://stwcas.okstate.edu/idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-library-okstate.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ou",
            "name": "The University of Oklahoma [Test]",
            "description": '<a href="https://www.ou.edu">The University of Oklahoma</a> | <a href="https://libraries.ou.edu">University Libraries</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://shib.ou.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ou.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "oxford",
            "name": "University of Oxford [Test]",
            "description": "",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "via-orcid",
            "orcid_record_verified_source": "ORCID Integration at the University of Oxford",
        },
        {
            "_id": "pu",
            "name": "Princeton University [Test]",
            "description": 'A research project management and sharing tool provided to the Princeton University research community by the <a href="https://library.princeton.edu/">Princeton University Library</a> and the <a href="https://researchdata.princeton.edu/">Princeton Research Data Service</a>. Projects must abide by University guidelines for <a href="https://ria.princeton.edu/research-data-security">Research Data Security and Privacy</a> and <a href="https://oit.princeton.edu/policies/information-security">Information Security</a> | <a href="https://github.com/CenterForOpenScience/cos.io/blob/master/TERMS_OF_USE.md">OSF Terms of Use</a> | <a href="https://github.com/CenterForOpenScience/cos.io/blob/master/PRIVACY_POLICY.md">OSF Privacy Policy</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://idp.princeton.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-pu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "purdue",
            "name": "Purdue University [Test]",
            "description": 'This open scholarship platform is provided by <a href="https://www.lib.purdue.edu/">Purdue University Libraries</a> in partnership with the University\'s <a href="https://www.purdue.edu/gradschool/">Graduate School</a>, <a href="https://www.purdue.edu/research/oevprp/regulatory-affairs/">Regulatory Affairs</a>, and <a href="https://www.purdue.edu/provost/researchIntegrity/">Research Integrity Office</a>.<br><br>All projects must adhere to Purdue\'s <a href="https://www.purdue.edu/policies/information-technology/viib8.html#statement">Information security</a>, <a href="https://www.purdue.edu/policies/academic-research-affairs/ic1.html">Human subjects research</a> policies, and related <a href="https://www.purdue.edu/securepurdue/data-handling/index.php">data classification and handling procedures</a>. Associated guidance on regulations is available via the <a href="https://www.purdue.edu/research/oevprp/regulatory-affairs/responsible-conduct.php">Responsible Conductof Research website</a> and the <a href="https://www.purdue.edu/provost/researchIntegrity/">Research Integrity Office</a>. For questions and support please reach out to <a href="mailto:riboehm@purdue.edu">Purdue\'s OSF contact</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.purdue.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "sc",
            "name": "University of South Carolina Libraries [Test]",
            "description": 'Brought to you by <a href="http://library.sc.edu/">University Libraries</a> at the University of South Carolina.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://cas.auth.sc.edu/cas/idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-sc.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "temple",
            "name": "Temple University [Test]",
            "description": 'Projects must abide by the <a href="https://computerservices.temple.edu/classification-and-handling-protected-data">University Classification and Handling of Protected Data</a> and <a href="https://computerservices.temple.edu/guidelines-storing-and-using-personally-identifiable-information-non-production-environments">Guidelines for Storing and Using Personally Identifiable Information in Non-Production Environments</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://fim.temple.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-temple.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "thepolicylab",
            "name": "The Policy Lab at Brown University [Test]",
            "description": 'The Policy Lab at Brown University conducts applied research to improve public policy in Rhode Island and beyond.<br />Learn more at <a href="https://thepolicylab.brown.edu/">thepolicylab.brown.edu</a> and tune into our podcast, <a href="https://thirtythousandleagues.com/">30,000 Leagues</a>.',
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf-thepolicylab.cos.io"],
            "email_domains": ["policylab.io"],
            "delegation_protocol": "",
        },
        {
            "_id": "thelabatdc",
            "name": "The Lab @ DC",
            "description": 'The Lab @ DC is an entity of the <a href="https://mayor.dc.gov/">Executive Office of the Mayor of the District of Columbia Government</a>. We work in the <a href="https://oca.dc.gov/">Office of the City Administrator</a> and in partnership with a network of universities and research centers to apply the scientific method into day-to-day governance.',
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["dc.gov"],
            "delegation_protocol": "",
        },
        {
            "_id": "theworks",
            "name": "The Works Research Institute [Test]",
            "description": "The Works Research Institute",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": ["theworks.info"],
            "delegation_protocol": "",
        },
        {
            "_id": "tufts",
            "name": "Tufts University [Test]",
            "description": '<a href="http://researchguides.library.tufts.edu/RDM">Research Data Management &#64; Tufts</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shib-idp.tufts.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-tufts.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ua",
            "name": "University of Arizona [Test]",
            "description": 'A service supported by the <a href="http://www.library.arizona.edu/">University of Arizona Libraries</a>. For more information, please refer to the <a href="http://data.library.arizona.edu/osf">UA Data Management Page</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:arizona.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ua.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ubc",
            "name": "University of British Columbia [Test]",
            "description": 'Users are reminded to ensure their use of this service is in compliance with all <a href="https://universitycounsel.ubc.ca/policies/">UBC Policies and Standards</a>. Please refer specifically to <a href="https://universitycounsel.ubc.ca/files/2015/08/policy85.pdf">Policy 85</a>, <a href="https://universitycounsel.ubc.ca/files/2013/06/policy104.pdf">Policy 104</a>, and the <a href="https://cio.ubc.ca/node/1073">Information Security Standards</a>. Find out more about <a href="http://openscience.ubc.ca">OSF</a>. Get help with <a href="https://researchdata.library.ubc.ca/">Research Data Management</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://authentication.stg.id.ubc.ca")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ubc.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uc",
            "name": "University of Cincinnati [Test]",
            "description": 'In partnership with the <a href="https://research.uc.edu/home/officeofresearch/administrativeoffices.aspx">Office of Research</a>, <a href="https://www.libraries.uc.edu/">UC Libraries</a> and <a href="https://www.uc.edu/ucit.html">IT&#64;UC</a>. Projects must abide by <a href="http://www.uc.edu/infosec/policies.html">Security (9.1.27) and Data Protection (9.1.1) Policies.</a> Learn more by visiting <a href="https://libraries.uc.edu/digital-scholarship/data-services.html">Research Data & GIS services</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.uc.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-uc.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ucla",
            "name": "UCLA [Test]",
            "description": 'A research data service provided by the <a href="https://www.library.ucla.edu/">UCLA Library</a>. Please do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. For assistance please contact <a href="mailto:data@library.ucla.edu">data@library.ucla.edu</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:ucla.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ucla.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ucsd",
            "name": "University of California San Diego [Test]",
            "description": 'This service is supported on campus by the UC San Diego Library for our research community. Do not use this service to store or transfer personally identifiable information, personal health information, or any other controlled unclassified information. For assistance please contact the Library\'s Research Data Curation Program at <a href="mailto:research-data-curation@ucsd.edu">research-data-curation@ucsd.edu</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:ucsd.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ucsd.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ucr",
            "name": "University of California Riverside [Test]",
            "description": 'Policy prohibits storing PII or HIPAA data on this site, please see C&amp;C\'s <a href="http://cnc.ucr.edu/security/researchers.html">security site</a> for more information.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:ucr.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ucr.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uct",
            "name": "University of Cape Town [Test]",
            "description": '<a href="http://www.lib.uct.ac.za/">UCT Libraries</a>, <a href="http://www.eresearch.uct.ac.za/">UCT eResearch</a> &amp; <a href="http://www.icts.uct.ac.za/">ICTS</a> present the UCT OSF institutional service to UCT affiliated students, staff and researchers. The UCT OSF facility should be used in conjunction with the institution\'s <a href="http://www.digitalservices.lib.uct.ac.za/dls/rdm-policy">Research Data Management (RDM) Policy</a>, <a href="https://www.uct.ac.za/downloads/uct.ac.za/about/policies/UCTOpenAccessPolicy.pdf">Open Access Policy</a> and <a href="https://www.uct.ac.za/downloads/uct.ac.za/about/policies/UCTOpenAccessPolicy.pdf">IP Policy</a>. Visit the <a href="http://www.digitalservices.lib.uct.ac.za/">UCT Digital Library Services</a> for more information and/or assistance with <a href="http://www.digitalservices.lib.uct.ac.za/dls/rdm">RDM</a> and <a href="http://www.digitalservices.lib.uct.ac.za/dls/data-sharing-guidelines">data sharing</a>. We also encourage the use of UCT Libraries\'s Data Management Planning tool, <a href="http://dmp.lib.uct.ac.za/about_us">DMPonline</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "http://adfs.uct.ac.za/adfs/services/trust"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-uct.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "umb",
            "name": "University of Maryland, Baltimore [Test]",
            "description": 'This research data management service is supported by the <a href="https://www2.hshsl.umaryland.edu/cdabs/">Center for Data and Bioinformtion Services</a> at the <a href="https://www.hshsl.umaryland.edu/">Health Sciences and Human Services Library</a>. This platform is not intended for the storage of PII or PHI.<br><a href="https://www.umaryland.edu/policies-and-procedures/library/research/policies/iv-9901a.php">UMB Policy Regarding Ownership, Management, and Sharing of Research Data</a> | For questions contact <a href="mailto:data@hshsl.umaryland.edu">data@hshsl.umaryland.edu</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://webauth.umaryland.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-umb.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "umd",
            "name": "University of Maryland [Test]",
            "description": "Here goes the description of your institution.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:umd.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ugent",
            "name": "Universiteit Gent [Test]",
            "description": None,
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://ideq.ugent.be/simplesaml/saml2/idp/metadata.php"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ugent.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ugoe",
            "name": "University of Göttingen [Test]",
            "description": 'In partnership with <a href="https://www.sub.uni-goettingen.de/">Göttingen State and University Library</a>, the <a href="http://www.eresearch.uni-goettingen.de/">Göttingen eResearch Alliance</a> and the <a href="https://www.gwdg.de/">Gesellschaft für wissenschaftliche Datenverarbeitung Göttingen</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shibboleth-idp.uni-goettingen.de/uni/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-ugoe.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uit",
            "name": "UiT The Arctic University of Norway [Test]",
            "description": "UiT The Arctic University of Norway is a medium-sized research "
            "university that contributes to knowledge-based development at the "
            "regional, national and international level.",
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf-uit.cos.io"],
            "email_domains": ["uit.no"],
            "delegation_protocol": "",
        },
        {
            "_id": "unc",
            "name": "University of North Carolina at Chapel Hill [Test]",
            "description": 'This service is supported by <a href="https://odum.unc.edu/">The Odum Institute for Research in Social Science</a> and <a href="https://library.unc.edu">University Libraries at the University of North Carolina at Chapel Hill</a>. Please do not store or transfer personally identifiable information, personal health information, or any other sensitive or proprietary data in the OSF. Projects should follow applicable <a href="https://unc.policystat.com/">UNC policies</a>. Contact the <a href="mailto:odumarchive@unc.edu">Odum Institute Data Archive</a> with any questions.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:unc.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-unc.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "universityofkent",
            "name": "University of Kent [Test]",
            "description": 'Collaboration Platform for University of Kent Research | <a href="https://www.kent.ac.uk/governance/policies-and-procedures/documents/Information-security-policy-v1-1.pdf">Information Security policy</a> | <a href="mailto:researchsupport@kent.ac.uk">Help and Support</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://sso.id.kent.ac.uk/idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-universityofkent.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uol",
            "name": "University of London [Test]",
            "description": "A research project management and publication platform for the University of London research community",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://idp.uolia.london.ac.uk/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uom",
            "name": "University of Manchester [Test]",
            "description": 'OSF is currently only supported for FBMH Core Facility users, for further information contact <a href="mailto:danielle.owen@manchester.ac.uk">danielle.owen@manchester.ac.uk</a>. <a href="https://www.manchester.ac.uk/discover/privacy-information/">University of Manchester Privacy Policy</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://beta.shib.manchester.ac.uk/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "usc",
            "name": "University of Southern California [Test]",
            "description": 'Projects must abide by <a href="http://policy.usc.edu/info-security/">USC\'s Information Security Policy</a>. Data stored for human subject research repositories must abide by <a href="http://policy.usc.edu/biorepositories/">USC\'s Biorepository Policy</a>. The OSF may not be used for storage of Personal Health Information that is subject to <a href="http://policy.usc.edu/hipaa/">HIPPA regulations</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:usc.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-usc.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "ush",
            "name": "Universal Sustainability Hub [Test]",
            "description": '<a href="https://uvers.ac.id/">Universal Sustainability Hub for Universal Family</a>',
            "login_url": None,
            "logout_url": None,
            "domains": ["test-osf-ush.cos.io"],
            "email_domains": ["uvers.ac.id"],
            "delegation_protocol": "",
        },
        {
            "_id": "utdallas",
            "name": "The University of Texas at Dallas [Test]",
            "description": 'In partnership with the Office of Research. Learn more about <a href="https://data.utdallas.edu/">UT Dallas resources for computational and data-driven research</a>. Projects must abide by university security and data protection policies.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://idp.utdallas.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-utdallas.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uva",
            "name": "University of Virginia [Test]",
            "description": 'In partnership with the <a href="http://www.virginia.edu/vpr/">Vice President for Research</a>, <a href="http://dsi.virginia.edu">Data Science Institute</a>, <a href="https://www.hsl.virginia.edu">Health Sciences Library</a>, and <a href="http://data.library.virginia.edu">University Library</a>. Learn more about <a href="http://cadre.virginia.edu">UVA resources for computational and data-driven research</a>. Projects must abide by the <a href="http://www.virginia.edu/informationpolicy/security.html">University Security and Data Protection Policies</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shibidp-test.its.virginia.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-virginia.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uw",
            "name": "University of Washington [Test]",
            "description": 'This service is supported by the University of Washington Libraries. Do not use this service to store or transfer personally identifiable information or personal health information. Questions? Email the Libraries Research Data Services Unit at <a href="mailto:libdata@uw.edu">libdata@uw.edu</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:washington.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "uwstout",
            "name": "University of Wisconsin - Stout [Test]",
            "description": 'A Research Project and File Management Tool for the UW-Stout Community: <a href="https://wwwcs.uwstout.edu/rs/index.cfm">Office of Research and Sponsored Programs</a> | <a href="https://wwwcs.uwstout.edu/lib/">University Library</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://smidp.uwstout.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-uwstout.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "vcu",
            "name": "Virginia Commonwealth University [Test]",
            "description": 'This service is supported by the VCU Libraries and the VCU Office of Research and Innovation for our research community. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), or any other controlled unclassified information (CUI). VCU\'s policy entitled "<a href="http://www.policy.vcu.edu/sites/default/files/Research%20Data%20Ownership,%20Retention,%20Access%20and%20Securty.pdf">Research Data Ownership, Retention, Access and Security</a>" applies. For assistance please contact the <a href="https://www.library.vcu.edu/services/data/">VCU Libraries Research Data Management Program</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "https://shibboleth.vcu.edu/idp/shibboleth"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-research-vcu.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "vt",
            "name": "Virginia Tech [Test]",
            "description": 'Made possible by the <a href="https://www.lib.vt.edu">University Libraries</a> in partnership with <a href="https://secure.hosting.vt.edu/www.arc.vt.edu/">Advanced Research Computing</a> and the <a href="https://research.vt.edu/">Office of the Vice President for Research</a>. Using the Virginia Tech login to OSF provides your name and VT email address to the Center for Open Science. Please see their <a href="https://github.com/CenterForOpenScience/cos.io/blob/master/TERMS_OF_USE.md">terms of service</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("urn:mace:incommon:vt.edu")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "vua",
            "name": "Vrije Universiteit Amsterdam [Test]",
            "description": 'A Research Data Management Tool for the Vrije Universiteit Amsterdam Research Community. <a href="https://osf.io/abwzm/wiki/home/">VU OSF Getting Started Guide</a> | <a href="https://vu.nl/en/employee/research-data-support">VU Research Data Support</a>',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component(
                    "http://stsfed.test.vu.nl/adfs/services/trust"
                )
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-vua.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "wustl",
            "name": "Washington University in St. Louis [Test]",
            "description": 'This service is supported by the <a href="https://library.wustl.edu">Washington University in St. Louis Libraries</a>. Please abide by the University policy on <a href="https://informationsecurity.wustl.edu/resources/information-security-solutions/data-classification/">information security</a>. Do not use this service to store or transfer personally identifiable information (PII), personal health information (PHI), or any other controlled unclassified information (CUI). | For assistance please contact the <a href="http://gis.wustl.edu/dgs">WU Libraries Data & GIS Services</a>.',
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("https://login.wustl.edu/idp/shibboleth")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("https://test.osf.io/goodbye")
            ),
            "domains": ["test-osf-wustl.cos.io"],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
    ],
    "local": [
        {
            "_id": "osftype0",
            "name": "Fake CAS Institution",
            "description": "Fake OSF Institution Type 0. Its SSO is done via CAS (pac4j impl) where OSF-CAS serves as "
            "the CAS client and the institution as the CAS server.",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "cas-pac4j",
        },
        {
            "_id": "osftype1",
            "name": 'Fake "via-ORCiD" Institution',
            "description": "Fake OSF Institution Type 1. This institution uses ORCiD SSO for login and its user "
            "affiliation is retrieved from ORCiD public record.",
            "login_url": None,
            "logout_url": None,
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "via-orcid",
            "orcid_record_verified_source": "OSF Integration",
        },
        {
            "_id": "osftype2",
            "name": "Fake SAML Institution - Standard",
            "description": "Fake OSF Institution Type 2. Its SSO is done via SAML (Shibboleth impl) where OSF-CAS "
            "serves as the SP and the institution as the IdP.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("type-2-fake-saml-idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("http://localhost:5000/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
            "orcid_record_verified_source": "",
        },
        {
            "_id": "osftype3",
            "name": "Fake SAML Institution - Shared SSO Primary (Criteria: EQUALS_TO)",
            "description": "Fake OSF Institution Type 3. Its SSO is done via SAML (Shibboleth impl) where OSF-CAS "
            "serves as the SP and the institution as the IdP. This institution is a primary one that "
            "provides shared SSO to secondary institutions.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("type-3-fake-saml-idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("http://localhost:5000/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "osftype4",
            "name": "Fake SAML Institution - Shared SSO Secondary (Criteria: EQUALS_TO)",
            "description": "Fake OSF Institution Type 3. Its SSO is done via SAML (Shibboleth impl) where OSF-CAS "
            "serves as the SP and the institution as the IdP. This institution is a secondary one that "
            "uses a primary institution's SSO.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("type-4-fake-saml-idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("http://localhost:5000/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "osftype5",
            "name": "Fake SAML Institution - Selective SSO",
            "description": "Fake OSF Institution Type 3. Its SSO is done via SAML (Shibboleth impl) where OSF-CAS "
            "serves as the SP and the institution as the IdP. This institution only allows a subset of "
            "users to use SSO by releasing a special attribute for them.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("type-5-fake-saml-idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("http://localhost:5000/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
            "orcid_record_verified_source": "",
        },
        {
            "_id": "osftype6",
            "name": "Fake SAML Institution - Department I",
            "description": "Fake OSF Institution Type 3. Its SSO is done via SAML (Shibboleth impl) where OSF-CAS "
            "serves as the SP and the institution as the IdP. This institution provides the department "
            "attribute via an eduPerson attribute.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("type-6-fake-saml-idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("http://localhost:5000/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "osftype7",
            "name": "Fake SAML Institution - Department II",
            "description": "Fake OSF Institution Type 3. Its SSO is done via SAML (Shibboleth impl) where OSF-CAS "
            "serves as the SP and the institution as the IdP. This institution provides the department "
            "attribute via a customized attribute.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("type-7-fake-saml-idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("http://localhost:5000/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "osftype8",
            "name": "Fake SAML Institution - Shared SSO Primary (Criteria: CONTAINS)",
            "description": "Fake OSF Institution Type 8. Its SSO is done via SAML (Shibboleth impl) where OSF-CAS "
            "serves as the SP and the institution as the IdP. This institution is a primary one that "
            "provides shared SSO to secondary institutions.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("type-8-fake-saml-idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("http://localhost:5000/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
        {
            "_id": "osftype9",
            "name": "Fake SAML Institution - Shared SSO Secondary (Criteria: CONTAINS)",
            "description": "Fake OSF Institution Type 9. Its SSO is done via SAML (Shibboleth impl) where OSF-CAS "
            "serves as the SP and the institution as the IdP. This institution is a secondary one that "
            "uses a primary institution's SSO.",
            "login_url": SHIBBOLETH_SP_LOGIN.format(
                encode_uri_component("type-9-fake-saml-idp")
            ),
            "logout_url": SHIBBOLETH_SP_LOGOUT.format(
                encode_uri_component("http://localhost:5000/goodbye")
            ),
            "domains": [],
            "email_domains": [],
            "delegation_protocol": "saml-shib",
        },
    ],
}


if __name__ == "__main__":
    init_app(routes=False)
    main(default_args=False)
