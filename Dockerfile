FROM python:3.10-alpine AS blog-builder

RUN apk add --no-cache git
WORKDIR /build

COPY plugins /build/plugins
COPY requirements /build/requirements
RUN pip install --no-cache-dir virtualenv -r requirements/build.txt

COPY blog /build/blog
COPY overrides /build/overrides
COPY Makefile mkdocs.yml /build/
RUN mkdocs build


FROM nginx:alpine

RUN rm -rf /usr/share/nginx/html
COPY --from=blog-builder /build/site /usr/share/nginx/html
