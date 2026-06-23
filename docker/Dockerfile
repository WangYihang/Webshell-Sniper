# Target container for the Webshell-Sniper benchmark environment.
#
# Defaults to the canonical Docker Hub image. If you hit Docker Hub's anonymous
# pull rate limit, override PHP_IMAGE with a mirror (see .env.example).
ARG PHP_IMAGE=php:8.3-apache
FROM ${PHP_IMAGE}

# mysqli so the `db` feature can be exercised against the bundled MySQL service.
RUN docker-php-ext-install mysqli

COPY webroot/ /var/www/html/
RUN chown -R www-data:www-data /var/www/html
