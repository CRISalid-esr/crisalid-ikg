########################
Quickstart: development
########################
This guide will walk you through setting up the SVP Harvester project on a fresh Ubuntu 22.04 installation.


1. Install RabbitMQ
----------------------

.. tab-set::

    .. tab-item:: On platform

        To install RabbitMQ on your system, please follow the steps outlined in the `official RabbitMQ documentation <https://www.rabbitmq.com/docs/install-debian>`_.
        Once RabbitMQ is installed, enable the management interface by executing the following commands:

        .. code-block:: bash

            # Enable the management interface
            sudo rabbitmq-plugins enable rabbitmq_management

            # Restart RabbitMQ
            sudo systemctl restart rabbitmq-server

    .. tab-item:: On docker

        With Docker installed, use the following commands:

        .. code-block:: bash

            docker pull rabbitmq:3.13-management

            docker run -d --hostname my-rabbit --name rabbitmq --publish=15672:15672 --publish=5672:5672 rabbitmq:3.13-management



After completing these steps, access the management interface through your web browser by navigating to `localhost:15672`. You can log in using the default credentials: ``guest:guest``.

Install Neo4j
--------------

.. tab-set::

    .. tab-item:: On platform

        To install Neo4j on your system, please follow the steps outlined in the `official Neo4j documentation <https://neo4j.com/docs/operations-manual/current/installation/>`_.

    .. tab-item:: On docker

        With Docker installed, use the following commands:

        .. code-block:: bash

            docker pull neo4j:5-community

            docker run --name neo4j_main --publish=7474:7474 --publish=7687:7687 --env=NEO4J_AUTH=none   neo4j:5-community



Install Poetry
----------------
This project use poetry to manage dependencies.
The procedure to install poetry can be found here: https://python-poetry.org/docs/#installation

Set up the project
------------------

With poetry install the dependencies of the project:

.. code-block:: bash

        poetry install --sync --with development

At the root of the project, copy .env.example to .env

Start Rabbitmq and Neo4j, then start IKG:

.. code-block:: bash

    APP_ENV=DEV uvicorn app.main:app --reload