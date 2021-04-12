.PHONY: test
.PHONY: notebook
#ve = $(shell echo ${VIRTUAL_ENV\#\#*/})
ve = $(shell basename $(VIRTUAL_ENV))

test:
	echo $(ve)
ifeq ($(ve), emo20q-test) 
	python -m pytest
else
	echo "make sure to use the emo20q-test vm"
endif

notebook:
	echo $(ve)
ifeq ($(ve), emo20q-notebook) 
	$VIRTUAL_ENV/bin/jupyter notebook
else
	echo "make sure to use the emo20q-notebook vm"
endif
