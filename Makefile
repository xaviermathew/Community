PROJECT_DIR=`pwd`
VIRTUAL_ENV_ROOT=$(HOME)/virtual_env
VIRTUAL_ENV_NAME=community
PYTHON_PATH=$(VIRTUAL_ENV_ROOT)/$(VIRTUAL_ENV_NAME)/bin/python
CRONTAB_FILE=config/crontab/crontab

make_dirs:
	mkdir -p $(PROJECT_DIR)/logs/celery
	mkdir -p $(PROJECT_DIR)/pids/celery
	mkdir -p $(PROJECT_DIR)/pids/discord_listener
	mkdir -p $(PROJECT_DIR)/state
	touch $(PROJECT_DIR)/state/logrotate-state
swap:
	sudo /bin/dd if=/dev/zero of=/var/swap bs=1M count=$(expr $(grep MemTotal /proc/meminfo | awk '{print $2}') / 1024)
	sudo /sbin/mkswap /var/swap
	sudo chmod 600 /var/swap
	sudo /sbin/swapon /var/swap
pull:
	git pull
update_cron:
	crontab $(CRONTAB_FILE)
	sudo service cron restart
update_systemd:
	sudo cp config/systemd/* /etc/systemd/system/
	sudo systemctl daemon-reload
restart:
	sudo systemctl restart discord_listener
	sudo systemctl restart celery
stop:
	sudo systemctl stop discord_listener
	sudo systemctl stop celery
pip:
	pip install -r requirements.txt
fresh_code: pull pip make_dirs
deploy: fresh_code update_cron update_systemd restart
venv:
	sudo add-apt-repository universe
	sudo apt-get update
	sudo apt-get install -y python3.9
	sudo apt-get install -y python3-pip
	sudo apt-get install -y python-dev build-essential git virtualenvwrapper
	sudo apt-get install -y libpq-dev
	sudo apt install libcurl4-openssl-dev libssl-dev
	echo "export WORKON_HOME=~/virtual_env" >> $(HOME)/.bash_aliases
	echo "source /usr/share/virtualenvwrapper/virtualenvwrapper.sh" >> $(HOME)/.bash_aliases
	echo "export VISUAL=vim" >> $(HOME)/.bash_aliases
	echo "export EDITOR=vim" >> $(HOME)/.bash_aliases
	source $(HOME)/.bash_aliases && mkvirtualenv community --python `which python3.9`
models:
	$(PYTHON_PATH) manage.py inspectdb --database community 2>&1 | grep -v "^2021" | grep -v RuntimeWarning | sed -e "/AutoField()/s//AutoField(primary_key=True)/" | sed -e "/models.TextField()  # This field type is a guess./s//models.JSONField()/" | sed -e "/models.TextField(blank=True, null=True)  # This field type is a guess./s//models.JSONField(blank=True, null=True)/"> /tmp/dj_models.py
	$(PYTHON_PATH) manage.py inspectdb --database rainman 2>&1 | grep -v "^2021" | grep -v RuntimeWarning | sed -e "/AutoField()/s//AutoField(primary_key=True)/" | sed -e "/models.TextField()  # This field type is a guess./s//models.JSONField()/" | sed -e "/models.TextField(blank=True, null=True)  # This field type is a guess./s//models.JSONField(blank=True, null=True)/">> /tmp/dj_models.py
	mv /tmp/dj_models.py community/app/dj_models.py
	$(PYTHON_PATH) manage.py check
bootstrap: venv make_dirs fresh_code
