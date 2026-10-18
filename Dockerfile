
FROM nginxinc/nginx-unprivileged:alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY site/ /usr/share/nginx/html/

EXPOSE 8080

ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
