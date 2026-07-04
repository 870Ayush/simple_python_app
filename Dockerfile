# Multi-stage build — keeps the runtime image small and free of build tooling.
# (Showcases the image-hardening you did at Chubb: smaller image, smaller attack surface.)

# ---- build stage ----
FROM python:3.12-slim AS build
WORKDIR /app
COPY requirements.txt .
# Install deps into a wheelhouse so the runtime stage stays clean.
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime stage ----
FROM python:3.12-slim AS runtime
WORKDIR /app

# Copy only the installed packages from the build stage — no pip cache, no build junk.
COPY --from=build /install /usr/local
COPY app.py .

# Run as a non-root user (hardening).
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8080
ENTRYPOINT ["python"]
CMD ["app.py"]
