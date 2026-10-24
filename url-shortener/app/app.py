import os
import string

from flask import Flask, request, redirect, jsonify
import redis
import psycopg2

app = Flask(__name__)

# Define the 62 characters used for short codes (0-9, a-z, A-Z)
ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase
ALPHABET_SET = set(ALPHABET)

# Connect to Redis for fast lookups
cache = redis.Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    decode_responses=True,
)


def get_db():
    """Connect to PostgreSQL for permanent storage."""
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "db"),
        database=os.environ.get("POSTGRES_DB", "urlshortener"),
        user=os.environ.get("POSTGRES_USER", "postgres"),
        password=os.environ.get("POSTGRES_PASSWORD", "postgres"),
    )


def base62_encode(num):
    """Convert a database ID into a short alphanumeric string."""
    if num == 0:
        return ALPHABET[0]
    result = []
    while num > 0:
        num, remainder = divmod(num, 62)
        result.append(ALPHABET[remainder])
    return "".join(reversed(result))


def base62_decode(code):
    """Convert a short code back into the original database ID."""
    num = 0
    for char in code:
        if char not in ALPHABET_SET:
            return None
        num = num * 62 + ALPHABET.index(char)
    return num


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to verify app status."""
    return jsonify({"status": "healthy"}), 200


@app.route("/shorten", methods=["POST"])
def shorten_url():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "Missing url field"}), 400

    long_url = data["url"].strip()
    if not long_url:
        return jsonify({"error": "URL cannot be empty"}), 400

    # Save to PostgreSQL - the database assigns an auto-incrementing ID
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO urls (long_url) VALUES (%s) RETURNING id", (long_url,))
    url_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    # Encode the database ID into a short code
    short_code = base62_encode(url_id)

    # Cache the mapping for fast redirects later
    cache.set(short_code, long_url)

    return jsonify({
        "short_url": f"http://localhost:5000/{short_code}",
        "short_code": short_code
    }), 201


@app.route("/<short_code>", methods=["GET"])
def redirect_url(short_code):
    # Ignore browser favicon requests
    if short_code == "favicon.ico":
        return "", 204

    # 1. Check the fast cache first
    long_url = cache.get(short_code)
    if long_url:
        print("CACHE HIT", flush=True)
        return redirect(long_url, code=302)

    # Validate characters before querying the database
    decoded_id = base62_decode(short_code)
    if decoded_id is None:
        return jsonify({"error": "Invalid short code"}), 404

    # 2. Cache miss - fall back to the database
    print("CACHE MISS - querying database", flush=True)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT long_url FROM urls WHERE id = %s", (decoded_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if not result:
        return jsonify({"error": "Short URL not found"}), 404

    long_url = result[0]
    # Re-populate cache for subsequent requests
    cache.set(short_code, long_url)

    return redirect(long_url, code=302)


if __name__ == '__main__':
    # Listen on all container interfaces (0.0.0.0)
    app.run(host="0.0.0.0", port=5000, debug=True)