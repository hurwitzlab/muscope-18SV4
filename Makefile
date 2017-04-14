APP = muscope-18SV4
VERSION = 0.0.1
EMAIL = jklynch@email.arizona.edu

clean:
	find . \( -name \*.conf -o -name \*.out -o -name \*.log -o -name \*.param -o -name launcher-\* \) -exec rm {} \;

files-delete:
	files-delete $(CYVERSEUSERNAME)/applications/$(APP)-$(VERSION)

files-upload:
	files-upload -F . $(CYVERSEUSERNAME)/applications/$(APP)-$(VERSION)

apps-addupdate:
	apps-addupdate -F stampede/app.json

test:
	sbatch test.sh

jobs-submit:
	jobs-submit -F stampede/job.json

