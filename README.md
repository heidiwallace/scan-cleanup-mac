# scan-cleanup

`scan-cleanup` helps you clean up scanned PDFs (for example, old scanned documents) so the pages are straightened, cropped, cleaned up, and turned into a searchable PDF. It walks you through the process step by step:

1.  It pulls each page out of your PDF as an image.
2.  It opens a program called ScanTailor Advanced, already set up with good default settings, so you can look over and adjust each page.
3.  Once you close ScanTailor Advanced, it automatically checks that every page came out correctly.
4.  It puts the cleaned-up pages back together in the right order.
5.  It makes the text on the pages searchable and saves the finished PDF.

## Getting set up

This section only needs to be done once. It walks through installing a few free programs, plus `scan-cleanup` itself. Once it's done, skip down to "Cleaning up a PDF" for everyday use.

Every step below is run in the **Terminal** app. If it's not already open, find it in your Applications window or by searching for "Terminal" in Spotlight (the magnifying glass in the top-right corner of your screen, or press Cmd+Space).

Each gray box below is a command: click into the box to copy it, paste it into Terminal (Cmd+V), press Enter, and wait for it to finish before moving to the next one.

### Step 1: Install Homebrew

Homebrew is a tool that makes it easy to install other software on a Mac. If you're not sure whether you already have it, run:

``` bash
brew --version
```

If you see a version number printed back, Homebrew is already installed — skip ahead to Step 2. Otherwise, run:

``` bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow any on-screen instructions it gives you (it may ask for your Mac password, and that's expected — nothing shows on screen as you type it, so just type it and press Enter). When it finishes, run `brew --version` again to confirm you now see a version number.

### Step 2: Install ScanTailor Advanced

ScanTailor Advanced is the program you'll use to review and adjust each scanned page. There isn't a one-line install for it, so you'll build it from its source code — Homebrew handles the hard parts. Paste each of these lines into Terminal one at a time, waiting for each to finish before starting the next (the build step can take several minutes):

``` bash
brew install cmake ninja qt jpeg-turbo libpng libtiff
git clone https://github.com/ScanTailor-Advanced/scantailor-advanced.git
cmake -S scantailor-advanced -B scantailor-advanced/build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build scantailor-advanced/build
cmake --install scantailor-advanced/build --prefix "$(brew --prefix)"
```

**Optional**: You can read more about installing ScanTailor Advanced on a Mac <a href = "https://scantailor.net/download/#macos-guide">here</a>.

### Step 3: Install the other required programs

`scan-cleanup` also needs two more small programs: one that reads text out of scanned pages (Tesseract), and one that helps assemble the final PDF (Ghostscript). Install both with:

``` bash
brew install tesseract ghostscript
```

### Step 4: Install uv

`uv` is the tool `scan-cleanup` uses to set itself up and run. Install it with:

``` bash
brew install uv
```

(`scan-cleanup` also needs Python, version 3.12 or newer — but you don't need to install that yourself; `uv` will take care of it automatically the first time it's needed.)

### Step 5: Install scan-cleanup

Installing `scan-cleanup` uses Git, a program for downloading project code. macOS will typically offer to install this automatically the first time it's needed — if a window pops up asking to install developer tools, click **Install** and wait for it to finish, then continue below.

Install `scan-cleanup` itself:

``` bash
uv tool install git+https://github.com/heidiwallace/scan-cleanup-mac
```

That's it — `scan-cleanup` is now installed, ready to use from any folder, with no project folder to keep track of.

If you see a warning like `... is not on your PATH`, run this once (it's a one-time fix — you won't need to repeat it after future installs):

``` bash
uv tool update-shell
```

**Close this Terminal window and open a new one** afterward, so the `scan-cleanup` command is recognized. To check it worked, run:

``` bash
scan-cleanup --help
```

It should print usage instructions. If you see a message like "command not found," please contact us for further troubleshooting.

## Using scan-cleanup

In the commands below, replace anything in ALL CAPS with your own file or folder path — for example, `INPUT.pdf` becomes the actual path to your PDF, and `OUTPUT_DIRECTORY` becomes the folder you want the result saved in. The easiest way to get a path right is to type the command up to that point, then drag the file or folder from Finder directly into the Terminal window — it will fill in the correct path for you.

### Cleaning up a PDF

To clean up a single scanned PDF, run:

``` bash
scan-cleanup process INPUT.pdf OUTPUT_DIRECTORY
```

Replace `INPUT.pdf` with the path to your scanned PDF, and `OUTPUT_DIRECTORY` with the folder where you want the finished file saved. The finished file will appear as:

``` text
OUTPUT_DIRECTORY/INPUT_processed.pdf
```

If a file with that name already exists, you'll be asked to confirm before it gets replaced.

Shortly after you run the command, ScanTailor Advanced will open on its own with your pages already loaded and good default settings applied. Look through the pages, make any adjustments you'd like, then process all the pages and close the ScanTailor Advanced window. `scan-cleanup` will notice the window closed and automatically finish the job — assembling the pages and making the text searchable.

### If something goes wrong partway through

If ScanTailor Advanced closes but a page is missing or didn't come out right, `scan-cleanup` will stop and tell you where your in-progress files are being kept (this location is called the "workspace"). Fix the problem, then pick up where you left off with:

``` bash
scan-cleanup resume WORKSPACE OUTPUT_DIRECTORY
```

(Use the workspace location `scan-cleanup` showed you.) This reopens ScanTailor Advanced on the same project. Once you close it again, `scan-cleanup` will check the pages and finish the job.

### Cleaning up many PDFs at once

If you have a whole folder of scanned PDFs to clean up, you can process them one after another with a single command:

``` bash
scan-cleanup batch INPUT_DIRECTORY OUTPUT_DIRECTORY
```

ScanTailor Advanced will open once for each PDF in turn. If you need to stop partway through, you can simply run the same command again later — any PDF that's already been finished will be skipped automatically, so you'll pick up right where you left off. If you'd like to redo files that were already finished, add `--overwrite` to the command.
