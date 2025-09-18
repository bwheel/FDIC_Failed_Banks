from livereload import Server
import os


# Serve the current directory
def main():
    server = Server()

    # Watch for changes in HTML, CSS, JS, and DB files
    server.watch("*.html")
    server.watch("*.css")
    server.watch("*.js")
    server.watch("*.csv")

    # Serve current directory
    server.serve(root=f"{os.getcwd()}/docs", port=5500)


if __name__ == "__main__":
    main()
