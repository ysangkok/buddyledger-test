#!/usr/bin/env bash
''':'
set -o errexit
set -o pipefail
set -o nounset
set -o xtrace
cd "$( dirname "${BASH_SOURCE[0]}" )"
#if [ ! -e jython2.7.jar ]; then curl -L -o jython2.7.jar http://search.maven.org/remotecontent?filepath=org/python/jython-standalone/2.7.0/jython-standalone-2.7.0.jar; fi
if [ ! -e jython-install ]; then
    curl -L -o jython-installer-2.7.0.jar "http://search.maven.org/remotecontent?filepath=org/python/jython-installer/2.7.0/jython-installer-2.7.0.jar"
    java -jar jython-installer-2.7.0.jar -s -d "$PWD/jython-install"
    echo "python.security.respectJavaAccessibility = false" >> jython-install/registry
fi
if [ ! -e jython-install/Lib/site-packages/django ]; then
    ./jython-install/bin/pip install "django>=1.8.4,<1.9.0"
fi
if [ ! -e jython-install/Lib/site-packages/doj ]; then
    ./jython-install/bin/pip install "django-jython==1.8.0b2"
fi
if [ ! -e lib ]; then
    mkdir lib
fi
if [ ! -e lib/sqlite-jdbc-3.8.11.1.jar ]; then
    curl -L -o lib/sqlite-jdbc-3.8.11.1.jar "https://bitbucket.org/xerial/sqlite-jdbc/downloads/sqlite-jdbc-3.8.11.1.jar"
fi
if [ ! -e apache-ivy-2.4.0 ]; then curl -L http://apache.mesi.com.ar/ant/ivy/2.4.0/apache-ivy-2.4.0-bin-with-deps.tar.gz | tar zx; fi
JYTHONPATH=buddyledger/src/ exec ./jython-install/bin/jython "$0"
'''
import sys
import os.path
import glob
from zipfile import ZipFile
import unittest
from django.test import Client
import django
from buddyledger import settings as normal_settings
from django.conf import settings
from django.conf import global_settings

ARTIFACT_VERSION = "2.18"
ARTIFACT_ID = "htmlunit"
JARPATH = 'lib-' + ARTIFACT_VERSION

def download_htmlunit():
    if os.path.exists(JARPATH + "/{}-{}.jar".format(ARTIFACT_ID, ARTIFACT_VERSION)):
        return
    IVYPATH = "apache-ivy-2.4.0/ivy-2.4.0.jar"
    sys.path.append(IVYPATH)
    import org.apache.ivy.Main as Main

    #IVYSETTINGS_PATH="ivysettings.xml"
    #if not os.path.exists(IVYSETTINGS_PATH):
    #    with ZipFile(IVYPATH, 'r') as myzip:
    #        with open(IVYSETTINGS_PATH, "w") as f:
    #            f.write(myzip.read('org/apache/ivy/core/settings/ivysettings.xml'))

    Main.run(Main.getParser(), ["-dependency", "net.sourceforge.htmlunit", ARTIFACT_ID, ARTIFACT_VERSION, "-retrieve", JARPATH + "/[artifact]-[revision](-[classifier]).[ext]"])

def add_htmlunit_to_classpath():
    for jar in glob.glob(os.path.join(JARPATH,"*.jar")):
        sys.path.append(jar)

class SimpleTest(unittest.TestCase):
    def setUp(self):
        import com.gargoylesoftware.htmlunit.WebClient as WebClient
        webclient = WebClient()
        self.client = Client()

    def test_details(self):
        response = self.client.get('/customer/details/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['customers']), 5)

#def gotopage():
#    print('hello, I will visit Google')
#    url = 'http://google.com'
#    page = webclient.getPage(url)
#    print(page)

if __name__ == "__main__":
    class Config(object):
        def __getattr__(self, name):
            if name == "DATABASES": return {'default': {'ENGINE': 'doj.db.backends.sqlite'}}
            try:
                return getattr(normal_settings, name)
            except AttributeError:
                return getattr(global_settings, name)
    settings.configure(Config())
    django.setup()

    download_htmlunit()
    add_htmlunit_to_classpath()
    unittest.main()
