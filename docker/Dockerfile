# Target container for the Webshell-Sniper benchmark environment.
#
# Defaults to the canonical Docker Hub image. If you hit Docker Hub's anonymous
# pull rate limit, override PHP_IMAGE with a mirror (see .env.example).
ARG PHP_IMAGE=php:8.3-apache
FROM ${PHP_IMAGE}

# mysqli + pdo_pgsql so both the MySQL and PostgreSQL `db` backends can be
# exercised against the bundled database services.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends libpq-dev; \
    rm -rf /var/lib/apt/lists/*; \
    docker-php-ext-install mysqli pdo_pgsql

COPY webroot/ /var/www/html/
RUN chown -R www-data:www-data /var/www/html
