pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: python
    image: python:3.10
    command:
    - cat
    tty: true
"""
        }
    }

    environment {
        VAULT_ADDR     = 'http://192.168.65.131:18200'
        VAULT_SECRET   = 'customers/acme'
        VAULT_KEY      = 'credentials'
        VAULT_SUBKEY   = 'password'
        AWX_URL        = 'http://192.168.65.131:8081'
        AWX_CRED_NAME  = 'Vault (Dev)'
        VAULT_USERNAME = 'devops'
        VAULT_PASSWORD = credentials('vault_userpass_secret')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Debug Vars') {
            steps {
                sh '''
                  echo "🔍 Debugging Environment Variables:"
                  echo "VAULT_ADDR=$VAULT_ADDR"
                  echo "VAULT_SECRET=$VAULT_SECRET"
                  echo "VAULT_KEY=$VAULT_KEY"
                  echo "VAULT_SUBKEY=$VAULT_SUBKEY"
                  echo "AWX_URL=$AWX_URL"
                  echo "AWX_CRED_NAME=$AWX_CRED_NAME"
                  echo "VAULT_USERNAME=$VAULT_USERNAME"
                  if [ -n "$VAULT_PASSWORD" ]; then
                    echo "VAULT_PASSWORD is set (hidden)"
                  else
                    echo "VAULT_PASSWORD is NOT set ❌"
                  fi
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                container('python') {
                    sh '''
                      pip install --upgrade pip
                      pip install requests hvac
                    '''
                }
            }
        }

        stage('Run Script') {
            steps {
                container('python') {
                    sh '''
                      python vault_awx_update.py
                    '''
                }
            }
        }
    }

    post {
        success {
            echo '✅ AWX credential updated successfully.'
        }
        failure {
            echo '❌ Job failed. Check logs above.'
        }
    }
}
