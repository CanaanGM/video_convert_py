import jwt, datetime, tomli
from flask import Flask, request
from flask_mysqldb import MySQL

server = Flask(__name__)
mysql = MySQL(server)

def load_config():
    """
    loads the config file
    """
    with open("auth_config.toml", mode="rb") as config_file:
        config = tomli.load(config_file)
    return config

config = load_config()
def set_mysql_configuration(db_config):
    """
    sets mySql config
    """
    server.config["MYSQL_HOST"] = db_config.get("MYSQL_HOST")
    server.config["MYSQL_USER"] = db_config.get("MYSQL_USER")
    server.config["MYSQL_PASSWORD"] = db_config.get("MYSQL_PASSWORD")
    server.config["MYSQL_DB"] = db_config.get("MYSQL_DB")
    server.config["MYSQL_PORT"] = db_config.get("MYSQL_PORT")

set_mysql_configuration( config.get("mysql_config"))
# print(server.config, end="\n")

def create_jwt(username, secret, authz):
    """
    authz -> if the user is admin or not
    creates and returns a token
    """
    return jwt.encode(
        {
            "username":username,
            "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1),
            "iat": datetime.datetime.utcnow(),
            "admin": authz,
        },
        secret,
        algorithm="HS256",
    )

# print(config.get("jwt_secret"))

@server.route("/login", method=["POST"])
def login():
    auth = request.authorization
    if not auth:
        return "messing creds", 401

    cur = mysql.connection.cursor()
    res = cur.execute(
        "SELECT email, password FROM user WHERE email=%s", (auth.username, auth.password)
    )

    if res > 0:
        user_row  = cur.fetchone()
        email, password = user_row

        if auth.username != email or auth.password != password:
            return "invalid creds", 401
        else:
            return create_jwt(auth.username, config.get("jwt_secret"), True )

    else:
        return "invalid creds", 401


@server.route("/validate", method=["post"])
def validate():
    """
    validates the token
    """
    encoded_jwt = request.headers["Authorization"]

    if not encoded_jwt:
        return "invalid creds", 401

    encoded_jwt = encoded_jwt.split(" ")[1] 
    try:
        decoded = jwt.decode(
            encoded_jwt,
            config.get("jwt_secret"),
            algorithm=["HS256"]
        )
    except:
        return "not authorized", 403
    return decoded, 200
     
if __name__ == "__main__":
    server.run(host="0.0.0.0", port=7878)
