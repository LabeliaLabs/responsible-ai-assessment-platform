# Readme 

## Installation


- Clone the project:

  ```console
  git clone git@framagit.org:labelia-labs/pf-assessment-dsrc.git
  ```

- Create `.env.dev` from `env_dev_template`:

  ```console
  cp env_dev_template .env.dev
  ```

- Replace variables in the .env.dev file

- Build Docker image and start it:

  ```console
  docker-compose up --build
  ```

- Migrations

  ```
  docker-compose exec questionnaire-grpc ./manage.py migrate
  ```
