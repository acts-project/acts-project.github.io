## <a name="admin-corner">Administrator's corner</a>

This section gives useful information to the administrators of the Acts project. For normal developers the sections below are irrelevant.

### <a name="tag-release">Make a new Acts release</a>

In order to release a new version of Acts the following steps need to be taken:

1. Check out all open JIRA issues for the next release in <a href="https://its.cern.ch/jira/projects/ACTS/versions/">JIRA</a>.
2. Create a new branch called <tt>release-X.YY.ZZ</tt> branching off from <tt>origin/master</tt>.
3. In this branch, update the <tt>ACTS_VERSION</tt> variable in the top-level CMakeLists.txt file to <tt>X.YY.ZZ</tt> and commit the change.
4. Pushing this commit to the remote repository should trigger a CI build. Make sure that everything compiles without any warnings and all tests look fine.
5. Create a new annotated tag locally. The tag should have the format <tt>vX.YY.ZZ</tt> and an associated tag message 'version vX.YY.ZZ'.
6. Push the tag to the remote repository. This should trigger a CI job which rebuilds to documentation and deploys it together with a tar file of the source code to the Acts webpage. Make sure that the new release appears under the **Releases** section on the <a href="http://acts.web.cern.ch/ACTS/">Acts webpage</a>.
7. If there is not yet a JIRA version for the next minor release, create it in the <a href="https://its.cern.ch/jira/plugins/servlet/project-config/ACTS/versions">JIRA project administration</a> area (e.g. if 1.23.02 was just released, version 1.23.03 should exist in JIRA for the next minor release for bug fixes).
8. Got to the <a href="https://its.cern.ch/jira/projects/ACTS/versions/">Acts Releases page in JIRA</a> and release the version. Make sure that a correct release data is set and that all open issues get moved to the next major/minor release.
9. From the JIRA release page, copy (all) the HTML code for the release notes. Login to lxplus using the service account <tt>atsjenkins</tt> (<tt>ssh atsjenkins@lxplus.cern.ch</tt>). Create the file <tt>~/www/ACTS/vX.YY.ZZ/ReleaseNotes.html</tt> with the copied HTML code for the release notes. Please make sure that _sub_-tasks appear as nested lists (JIRA unfortunately puts them all on one level in alphabetical order).
10. Check that the release notes appear on the <a href="http://acts.web.cern.ch/ACTS/">Acts webpage</a> and are available from the respective link in the **Releases** section.

### <a name="setup-jenkins">Setting up a Jenkins CI server</a>

The following steps explain on how to setup and configure a Jenkins server for continuous integration tests using the CERN openstack infrastructure.

1. Launch an openstack instance as described [here](https://clouddocs.web.cern.ch/clouddocs/tutorial_using_a_browser/index.html). The following settings are recommended:
  + flavor: m2.medium
  + boot from image: Ubuntu 16.04 LTS - x86_64
  + keypair: make sure to add a public ssh key using RSA encryption (**Note**: A DSA encrypted key does not work anymore with Ubuntu 16.04).
2. Login to your virtual machine, update the system and setup a user with root privileges:

        # login to the machine using the key-pair provided during instance creation
        ssh -i <public key> ubuntu@<vm-name>
        # update system 
        sudo apt-get update 
        sudo apt-get upgrade
        # fix locale warnings
        sudo locale-gen "en_GB.UTF-8"
        sudo dpkg-reconfigure locales
        # add Acts jenkins user with sudo privileges
        sudo adduser atsjenkins
        sudo usermod -aG sudo atsjenkins
        # to enable password authentication:
        # change PasswordAuthentication to 'yes' in '/etc/ssh/sshd_config'
        sudo service ssh restart
        # log out and re-log in as 'atsjenkins'
        # generate public-private key pair
        ssh-keygen -t rsa
        # add the public key from '~/.ssh/id_rsa.pub' to the GitLab atsjenkins account (under Profile Settings -> SSH keys)

3. Install docker and other required software:

        sudo apt-get install docker.io
        sudo apt-get install clang-format
        sudo apt-get install lcov
        sudo apt-get install mailutils
	      sudo apt install python-pip
        pip install --upgrade pip
        pip install --user requests

4. Install Jenkins (taken from [here](https://wiki.jenkins-ci.org/display/JENKINS/Installing+Jenkins+on+Ubuntu)):

        wget -q -O - https://pkg.jenkins.io/debian/jenkins-ci.org.key | sudo apt-key add -
        sudo sh -c 'echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
        sudo apt-get update
        sudo apt-get install jenkins
	      # allow jenkins to run docker without sudo
	      sudo usermod -aG docker jenkins
        sudo service jenkins start
	      sudo service docker restart
        
5. Setup a convenience alias and SSH credentials:

        # create an alias for executing commands as jenkins user
        cat >> ~/.bash_aliases << EOF
        > alias asjenkins="sudo -u jenkins"
        > EOF
        source ~/.bash_aliases
        # copy atsjenkins SSH credentials
	      asjenkins mkdir /var/lib/jenkins/.ssh
        sudo cp ~/.ssh/id_rsa ~/.ssh/id_rsa.pub /var/lib/jenkins/.ssh
        sudo chown jenkins /var/lib/jenkins/.ssh/id_rsa /var/lib/jenkins/.ssh/id_rsa.pub
        sudo chgrp jenkins /var/lib/jenkins/.ssh/id_rsa /var/lib/jenkins/.ssh/id_rsa.pub

6. Open firewall ports:

        # install firewall configuration tool
        sudo apt-get install firewalld
        sudo firewall-cmd --zone=public --add-port=8080/tcp --permanent
        sudo firewall-cmd --zone=public --add-service=http --permanent
        sudo firewall-cmd --reload

7. Configure the Jenkins instance through the web interface:
    1. Open the Jenkins Dashboard under http://&lt;VM-name&gt;:8080 in your browser and follow the instructions to unlock the Jenkins instance.
    2. Install the following Jenkins plugins:
        + git
        + gitlab
        + multijob
        + embeddable build status
        + rebuilder
        + timestamper
        + conditional build step
        + parametrized trigger
	+ build blocker
	+ credentials binder
    3. Create a Jenkins admin user with name `actsjenkins`, select a password and use `acts.jenkins@cern.ch` as email.
    4. Configure Jenkins instance:
        + Manage Jenkins -> Configure Global Security: enable "Allow anonymous read access"
        + Manage Jenkins -> Configure System 
            + Maven Project Configuration:
                + number of executors: 5
            + GitLab section:
                + Connection name: GitLab
                + GitLab host URL: https://gitlab.cern.ch
                + add credentials: use type "GitLab API token" and insert the private token from GitLab atsjenkins user (which can be found in GitLab under Profile settings -> Account -> Private token)
                + under advanced: tick "Ignore SSL certificate errors"
                + hit "Test Connection" which should return "success"
            + Jenkins location:
                + URL: http://&lt;VM-name&gt;.cern.ch:8080
                + email: acts.jenkins@cern.ch
            + Git plugin:
                + user.name: ACTS Jenkins
                + user.email: acts.jenkins@cern.ch
8. Configure the Jenkins CI jobs:

        # checkout the job configuration and helper scripts
        cd /var/lib/jenkins
        asjenkins git init
        asjenkins git remote add origin ssh://git@gitlab.cern.ch:7999/acts/jenkins-setup.git
        asjenkins git fetch
        asjenkins git checkout -t origin/master
        
        # fixing some credential settings which means manually copying the following part from 'credentials.xml.in'
        # <com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey ...>
        # ...
        # </com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey>
        # into 'credentials.xml' after the following line:
        # <java.util.concurrent.CopyOnWriteArrayList>
        
        # allow passing undefined parameters:
        # add '-Dhudson.model.ParametersAction.keepUndefinedParameters=true' to JAVA_ARGS in /etc/default/jenkins
        
        # restart the jenkins server
        sudo service jenkins restart
            
9. Setup kerberos authentication needed for updating the Acts webpage with new tags

        # authentication
        sudo apt install krb5-user
        sudo apt-get install openafs-client
        # generate keytab file
        ktutil
        ktutil:  addent -password -p atsjenkins@CERN.CH -k 1 -e aes256-cts-hmac-sha1-96
        ktutil:  addent -password -p atsjenkins@CERN.CH -k 1 -e arcfour-hmac
        ktutil:  wkt .keytab
        ktutil:  q
        sudo mv .keytab /etc/krb5_atsjenkins.keytab
        sudo chown jenkins /etc/krb5_atsjenkins.keytab
        sudo chgrp jenkins /etc/krb5_atsjenkins.keytab
        # download kerberos configuration
        sudo wget -O /etc/krb5.conf http://linux.web.cern.ch/linux/docs/krb5.conf
        # add "@daily ID=afstoken kinit --renew" to /etc/crontab
        
        # add the following to /etc/ssh/ssh_config
        #
        # HOST lxplus*
        #   ForwardX11 yes
        #   ForwardX11Trusted no
        #   GSSAPITrustDNS yes
        #   HashKnownHosts yes
        #   GSSAPIAuthentication yes
        #   GSSAPIDelegateCredentials yes
        
        # install mailutils for sending notifications
        sudo apt-get install mailutils

10. Some preparations for the CI jobs

    	sudo mkdir /build
	sudo chown jenkins /build
	sudo chgrp jenkins /build
	sudo ln -s /var/lib/jenkins/workspace/ACTS-MERGE /acts
	
/// @ingroup Contributing
