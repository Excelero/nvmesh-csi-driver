 #!/bin/bash
set +x

installType=$1

print_help() {
    echo "usage: "
    echo "To install the SDK run ./install sdk"
    echo "To install the CLI run ./install cli"
}

if [ -z "$installType" ]; then
    print_help
    exit 1
fi

echo "running install.sh, install type is: $installType"

if [ $installType = 'sdk' ];then
    echo 'installing NVMeshSDK'
    tmpDir='sdk_install'
    projectDir='NVMeshSDK'
elif [ $installType = 'cli' ];then
    echo 'installing NVMeshCLI'
    tmpDir='nvmesh_cli_install'
    projectDir='NVMeshCLI'
else
    echo 'Unknown install type, exiting'
    print_help
    exit 1
fi

python27=`which python2.7`
if [ $? -ne 0 ];then
    echo 'python2.7 in not installed, exiting'
    exit 2
fi

mkdir -p /tmp/$tmpDir/$projectDir
whoami=`whoami`

echo $whoami
sudo chown -R $whoami:$whoami /tmp/$tmpDir/

cd ../$projectDir

cp ./setup.py /tmp/$tmpDir/setup.py

cp -r ./* /tmp/$tmpDir/$projectDir

cd /tmp/$tmpDir/

echo "" > $projectDir.py

if [ $whoami = 'root' ];then
    $python27 ./setup.py install
else
    sudo -E bash -c "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib; $python27 ./setup.py install"
fi

sudo rm -rf /tmp/$tmpDir