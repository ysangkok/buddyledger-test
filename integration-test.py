#!/usr/bin/env bash
''':'
set -o errexit
set -o pipefail
set -o nounset
set -o xtrace
cd "$( dirname "${BASH_SOURCE[0]}" )"
#if [ ! -e jython2.7.jar ]; then curl -L -o jython2.7.jar http://search.maven.org/remotecontent?filepath=org/python/jython-standalone/2.7.0/jython-standalone-2.7.0.jar; fi
if [ ! -e jython-2.7 ]; then
    wget --no-clobber --trust-server-names -c "http://search.maven.org/remotecontent?filepath=org/python/jython-installer/2.7.0/jython-installer-2.7.0.jar"
    java -jar jython-installer-2.7.0.jar -s -d "$PWD/jython-2.7"
    echo "python.security.respectJavaAccessibility = false" >> jython-2.7/registry
fi
#./jython-2.7/bin/pip install -r buddyledger/requirements.txt
if [ ! -e jython-2.7/Lib/site-packages/django ]; then
    ./jython-2.7/bin/pip install "django>=1.8.4,<1.9.0"
fi
if [ ! -e jython-2.7/Lib/site-packages/doj ]; then
    ./jython-2.7/bin/pip install "django-jython==1.8.0b2"
fi
if [ ! -e lib ]; then
    mkdir lib
fi
if [ ! -e lib/sqlite-jdbc-3.8.11.1.jar ]; then
    curl -L -o lib/sqlite-jdbc-3.8.11.1.jar "https://bitbucket.org/xerial/sqlite-jdbc/downloads/sqlite-jdbc-3.8.11.1.jar"
fi
if [ ! -e apache-ivy-2.4.0 ]; then curl -L http://apache.mesi.com.ar/ant/ivy/2.4.0/apache-ivy-2.4.0-bin-with-deps.tar.gz | tar zx; fi
export CLASSPATH="lib/sqlite-jdbc-3.8.11.1.jar"
#./jython-2.7/bin/jython buddyledger/src/manage.py migrate
JYTHONPATH=buddyledger/src/:apache-ivy-2.4.0/ivy-2.4.0.jar exec ./jython-2.7/bin/jython "$0"
'''
import sys, os.path, glob, unittest, time, django, tempfile, re, subprocess
from zipfile import ZipFile
from django.test import Client
from buddyledger import settings as normal_settings
from django.conf import settings
from django.conf import global_settings
from django.core.management import execute_from_command_line
import pdb

ARTIFACT_VERSION = "2.18"
ARTIFACT_ID = "htmlunit"
JARPATH = 'lib-' + ARTIFACT_VERSION

def download_htmlunit():
    if os.path.exists(JARPATH + "/{}-{}.jar".format(ARTIFACT_ID, ARTIFACT_VERSION)):
        return
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
        self.webclient = WebClient()
        self.client = Client()

    def test_create_ledger(self):
        response = self.client.post('/ledger/create/', {'currency': 'AUD', 'name': 'test{}'.format(time.time())})
        self.assertEqual(response.status_code, 200)
        with tempfile.NamedTemporaryFile(delete=False) as f:
            for match in re.finditer(r'"//([^"]+)"', response.content):
                url = match.group(1)
                if not os.path.exists(url): subprocess.check_output(["wget", "--no-clobber", "--mirror", url], stderr=subprocess.STDOUT)
            f.write(response.content.replace("\"//", "\"file://{}/".format(os.getcwd())).replace("\"/static/","\"http://localhost:8080/buddyledger/static/".format(os.getcwd())))
            name = f.name
        page = self.webclient.getPage("file://" + f.name)
        #pdb.set_trace()
        alert = page.getFirstByXPath("//*[contains(@class, 'alert')]")
        assert alert is None, alert.asText()
        #self.assertEqual(len(response.context['customers']), 5)

#def gotopage():
#    print('hello, I will visit Google')
#    url = 'http://google.com'
#    page = webclient.getPage(url)
#    print(page)

if __name__ == "__main__":
    TESTDB = "testdb.sqlite3"
    class Config(object):
        def __getattr__(self, name):
            if name == "DATABASES": return {'default': {'NAME': os.path.join(os.getcwd(), TESTDB), 'ENGINE': 'doj.db.backends.sqlite'}}
            try:
                return getattr(normal_settings, name)
            except AttributeError:
                return getattr(global_settings, name)
    settings.configure(Config())
    #django.setup() # migrate does setup
    try:
        os.unlink(TESTDB)
    except:
        pass
    execute_from_command_line(["bogus", "migrate"])

    download_htmlunit()
    add_htmlunit_to_classpath()
    unittest.main()
