########################
Quickstart: deployment
########################
This guide will walk you through setting up the SVP Harvester project on a fresh Ubuntu 22.04 installation.


1. Install RabbitMQ
----------------------

To install RabbitMQ on your system, please follow the steps outlined in the `official RabbitMQ documentation <https://www.rabbitmq.com/docs/install-debian>`_.

Once RabbitMQ is installed, enable the management interface by executing the following commands:

.. code-block:: bash

    # Enable the management interface
    sudo rabbitmq-plugins enable rabbitmq_management

    # Restart RabbitMQ
    sudo systemctl restart rabbitmq-server

After completing these steps, access the management interface through your web browser by navigating to `localhost:15672`. You can log in using the default credentials: ``guest:guest``.


2. Install PostgreSQL
----------------------

Follow the steps outlined on `PostgreSQL's official documentation <https://www.postgresql.org/download/linux/ubuntu/>`_:

.. code-block:: bash

   # Add PostgreSQL repository
   sudo sh -c 'echo "deb https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
   wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
   sudo apt-get update

   # Install PostgreSQL
   sudo apt-get -y install postgresql-16

   # Create PostgreSQL database and user
   sudo -u postgres psql

In the PostgreSQL shell:

.. code-block:: sql

   CREATE DATABASE db;
   CREATE USER db_user WITH PASSWORD 'db_word';
   GRANT ALL PRIVILEGES ON DATABASE db TO db_user;
   ALTER DATABASE db OWNER TO db_user;

Following instructions....

Install Neo4j
--------------


Set up the project
------------------
