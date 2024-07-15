AWS_REGION ?= ap-southeast-2
AWS_ACCOUNT := cevo-dev

setup:
	pip install -r requirements.txt
test:
	bash tests/scripts/unit_tests.sh

collect:
	python cloudmapper.py collect --account ${AWS_ACCOUNT}

generate-excel: collect
	python cloudmapper.py generate_excel --account ${AWS_ACCOUNT}