# maxGPA

## Installation Package

This project can be shared as a local installation package. The package does
not require cloning this repository.

### Create the Package

From the repository root, run:

```sh
./CREATE_INSTALL_PACKAGE.sh
```

This creates:

```text
dist/MaxGPA_install_package.tar.gz
```

Send that `.tar.gz` file to the user who needs to run the app.

### Run the Package Without the Command Line

The user needs Docker Desktop installed and running.

After receiving the package, the user can double-click the package to extract it,
open the extracted `MaxGPA_install_package` folder, and then double-click:

```text
Start MaxGPA.command
```

That launcher starts Docker Compose and opens the app at:

```text
http://localhost:5001/
```

On macOS, the first launch may show a security prompt because the file came from
another computer. If that happens, right-click `Start MaxGPA.command`, choose
Open, then confirm that it should run.

### Run the Package From the Command Line

The command-line option does the same thing as the double-click launcher:

```sh
tar -xzf MaxGPA_install_package.tar.gz
cd MaxGPA_install_package
./INSTALL_AND_RUN.sh
```

The script builds and starts the Docker Compose services, then opens:

```text
http://localhost:5001/
```

### Stop the App

From inside the extracted `MaxGPA_install_package` directory, run:

```sh
docker compose down
```

### Port Notes

The Flask app is exposed on local port `5001`. MongoDB uses local port `27017`.
If Docker reports that port `27017` is already allocated, stop the other MongoDB
container or service before running the package.
