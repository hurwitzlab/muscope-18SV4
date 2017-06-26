APP = muscope-18SV4
VERSION = 0.0.2
EMAIL = jklynch@email.arizona.edu

clean:
	find . \( -name \*.conf -o -name \*.out -o -name \*.log -o -name \*.param -o -name *_launcher_jobfile\* \) -exec rm {} \;

files-delete:
	files-delete $(CYVERSEUSERNAME)/applications/$(APP)-$(VERSION)

files-upload:
	files-upload -F stampede/ $(CYVERSEUSERNAME)/applications/$(APP)-$(VERSION)

apps-addupdate:
	apps-addupdate -F stampede/app.json

deploy-app: clean files-delete files-upload apps-addupdate

test:
	sbatch test.sh

jobs-submit:
	jobs-submit -F stampede/job.json

container:
	rm -f singularity/muscope-18SV4.img
	sudo singularity create --size 2048 singularity/muscope-18SV4.img
	sudo singularity bootstrap singularity/muscope-18SV4.img singularity/muscope-18SV4.def

iput-container:
	irm muscope-18SV4.img
	iput -fKP singularity/muscope-18SV4.img

iget-container:
	iget -fKP muscope-18SV4.img
	mv muscope-18SV4.img stampede/

