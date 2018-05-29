APP = muscope-18SV4
VERSION = 2.0.0
EMAIL = jklynch@email.arizona.edu

clean:
	find . \( -name \*.conf -o -name \*.out -o -name \*.log -o -name \*.param -o -name launcher_jobfile_\* \) -exec rm {} \;

container:
	rm -f stampede2/$(APP).img
	sudo singularity create --size 1000 stampede2/$(APP).img
	sudo singularity bootstrap stampede2/$(APP).img singularity/$(APP).def
	sudo chown --reference=singularity/$(APP).def stampede2/$(APP).img

iput-container:
	iput -fK stampede2/$(APP).img

iget-container:
	iget -fK $(APP).img
	mv $(APP).img stampede2/
	irm $(APP).img

test:
	sbatch test.sh

submit-test-job:
	jobs-submit -F stampede2/job.json

submit-public-test-job:
	jobs-submit -F stampede2/public-job.json

container:
	rm -f stampede2/$(APP).img
	sudo singularity create --size 2000 stampede2/$(APP).img
	sudo singularity bootstrap stampede2/$(APP).img singularity/$(APP).def
	sudo chown --reference=singularity/$(APP).def stampede2/$(APP).img

iput-container:
	iput -fK stampede2/$(APP).img

iget-container:
	iget -fK $(APP).img
	mv $(APP).img stampede2/
	irm $(APP).img

test:
	sbatch test.sh

submit-test-job:
	jobs-submit -F stampede2/job.json

submit-public-test-job:
	jobs-submit -F stampede2/job-public.json

files-delete:
	files-delete -f $(CYVERSEUSERNAME)/applications/$(APP)-$(VERSION)

files-upload:
	files-upload -F stampede2/ $(CYVERSEUSERNAME)/applications/$(APP)-$(VERSION)

apps-addupdate:
	apps-addupdate -F stampede2/app.json

deploy-app: clean files-delete files-upload apps-addupdate

share-app:
	systems-roles-addupdate -v -u <share-with-user> -r USER tacc-stampede2-$(CYVERSEUSERNAME)
	apps-pems-update -v -u <share-with-user> -p READ_EXECUTE $(APP)-$(VERSION)

lytic-rsync-dry-run:
	rsync -n -arvzP --delete --exclude-from=rsync.exclude -e "ssh -A -t hpc ssh -A -t lytic" ./ :project/muscope/apps/$(APP)

lytic-rsync:
	rsync -arvzP --delete --exclude-from=rsync.exclude -e "ssh -A -t hpc ssh -A -t lytic" ./ :project/muscope/apps/$(APP)

lytic-rsync-direct:
	rsync -arvzP --delete --exclude-from=rsync.exclude -e "ssh -A -t lytic" ./ :project/muscope/apps/$(APP)
