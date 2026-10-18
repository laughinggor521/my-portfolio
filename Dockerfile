
FROM nginx:1.27-alpine

ENV PORT=8080

COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY site/ /usr/share/nginx/html/

EXPOSE 8080
