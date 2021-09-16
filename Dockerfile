FROM python:3-slim AS builder
ADD . /apps
WORKDIR /apps

# We are installing a dependency here directly into our app source dir
RUN pip install --target=/app -r requirements.txt

# A distroless container image with Python and some basics like SSL certificates
# https://github.com/GoogleContainerTools/distroless
FROM gcr.io/distroless/python3-debian10
COPY --from=builder /apps /apps
WORKDIR /apps
ENV PYTHONPATH /app
CMD ["/apps/diff.py"]
