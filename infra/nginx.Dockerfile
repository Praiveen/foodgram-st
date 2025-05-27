FROM nginx:1.25.4-alpine
COPY infra/nginx.conf /etc/nginx/conf.d/my_custom_site.conf
COPY docs/ /usr/share/nginx/html/api/docs/ 