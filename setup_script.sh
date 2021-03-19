#!/usr/bin/env sh
which virtualenv
RET=`echo $?`
echo virtualenv installed, $RET
if [ "$RET" = "1" ]
then
  sudo pip3 install virtualenv
fi

virtualenv --python=python3.7 env
env/bin/pip install -r requirements.txt
cp local_config/local_machine_configuration_sample.json local_config/local_machine_configuration.json
