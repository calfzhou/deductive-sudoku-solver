# Deductive Sudoku Solver - React App

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Available Scripts

In the project directory, you can run:

### `npm run solve-puzzle -- --help`

Runs the command-line sudoku solver.

E.g. to see minimal required rule levels, run:

``` bash
npm run solve-puzzle -- <PUZZLE-FILE> --show-steps evidence | grep -Eo '\[\w+@[0-9]+\]' | sort | uniq
```

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

### `npm test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

## Sudoku

### Terminology

A sudoku consists of **cells**, cells are grouped into **houses**. There are three different types of houses: **rows**, **columns** and **boxes** (under certain circumstances a cell can be seen as a house as well). Three boxes in a row are called a **chute** (a horizontal chute is a **floor**, a vertical chute is a **tower**) or a **band**. Cells are filled with **values**, the values present at the beginning of the game are called **givens**, possible values for unfilled cells are **candidates**. The whole sudoku area is sometimes called **grid**. If pencil and paper players write candidates into the grid these are sometimes called **pencil marks**, a grid with all candidates filled in is therefore a **pencil mark grid** or **PM**.

Rows and columns are numbered from 1 to 9 (left to right/top to bottom), a cell is specified by it's row and column (e.g.: r5c2 means the cell at row 5 and column 2; r57c2 means cells r5c2 and r7c2). Blocks are numbered from 1 to 9 too (top most floor from left to right, then the next floor and so on).

If two cells are in the same house (same row, same column, or same block) they are said to **see** each other, or to be **peers**. This is important in many techniques since two cells that see each other cannot have the same value.
