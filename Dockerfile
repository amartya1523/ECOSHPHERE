FROM node:22-bookworm-slim AS frontend

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM odoo:18.0

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx gettext-base ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY backend /mnt/extra-addons/eco_sphere_esg
COPY --from=frontend /app/frontend/dist /usr/share/nginx/html
COPY deploy/render/nginx.conf.template /etc/ecosphere/nginx.conf.template
COPY deploy/render/start.sh /usr/local/bin/ecosphere-render-start

RUN chmod +x /usr/local/bin/ecosphere-render-start \
    && mkdir -p /var/cache/nginx /var/log/nginx /run/nginx /etc/ecosphere \
    && chown -R odoo:odoo /mnt/extra-addons/eco_sphere_esg /usr/share/nginx/html /var/lib/odoo /var/cache/nginx /var/log/nginx /run/nginx /etc/ecosphere

USER odoo
EXPOSE 10000

CMD ["/usr/local/bin/ecosphere-render-start"]
