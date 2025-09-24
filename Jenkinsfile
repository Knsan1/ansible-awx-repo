pipeline {
    agent any

    environment {
        // Vault connection
        VAULT_ADDR     = 'http://192.168.65.131:18200'
        VAULT_SECRET   = 'customers/acme'
        VAULT_KEY      = 'credentials'
        VAULT_SUBKEY   = 'password'

        // AWX connection
        AWX_URL        = 'http://192.168.65.131:8081'
        AWX_CRED_NAME  = 'Vault (Dev)'

        // Shared login (Vault & AWX use same creds)
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

        stage('Setup Python Env') {
            steps {
                sh '''
                  python3 -m venv awx-env
                  source awx-env/bin/activate
                  pip install --upgrade pip
                  pip install requests hvac
                '''
            }
        }

        stage('Run Script') {
            steps {
                sh '''
                  source awx-env/bin/activate
                  python vault_awx_update.py
                '''
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
