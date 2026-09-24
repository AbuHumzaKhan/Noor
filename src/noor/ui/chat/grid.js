(() => {
  const table = document.getElementById("dataTable");
  const tbody = table?.querySelector("tbody");
  const thead = table?.querySelector("thead");
  const selection = document.getElementById("gridSelection");

  if (!table || !tbody || !thead) return;

  let selectedCell = null;

  function columnLabel(index) {
    let value = index + 1;
    let label = "";
    while (value > 0) {
      const remainder = (value - 1) % 26;
      label = String.fromCharCode(65 + remainder) + label;
      value = Math.floor((value - 1) / 26);
    }
    return label;
  }

  function selectCell(cell) {
    if (!cell || !cell.classList.contains("grid-cell")) return;
    table.querySelectorAll(".is-selected").forEach((element) => element.classList.remove("is-selected"));
    table.querySelectorAll(".is-selected-row, .is-selected-column").forEach((element) => {
      element.classList.remove("is-selected-row", "is-selected-column");
    });

    selectedCell = cell;
    cell.classList.add("is-selected");
    cell.parentElement?.querySelector(".grid-row-number")?.classList.add("is-selected-row");
    const columnIndex = Number(cell.dataset.columnIndex);
    thead.querySelector(`th[data-column-index="${columnIndex}"]`)?.classList.add("is-selected-column");

    const rowNumber = Number(cell.dataset.rowNumber) + 1;
    const header = cell.dataset.columnName || `Column ${columnIndex + 1}`;
    const value = cell.textContent || "";
    selection.textContent = `Row ${rowNumber} · ${columnLabel(columnIndex)} ${header} · ${value === "" ? "blank" : value}`;
  }

  function decorate() {
    const headerRow = thead.querySelector("tr");
    if (!headerRow) return;

    const existingCorner = headerRow.querySelector(".grid-corner");
    if (!existingCorner) {
      const corner = document.createElement("th");
      corner.className = "grid-corner";
      corner.scope = "col";
      corner.textContent = "#";
      corner.title = "Row numbers";
      headerRow.prepend(corner);
    }

    Array.from(headerRow.children).forEach((cell, index) => {
      if (cell.classList.contains("grid-corner")) return;
      const columnIndex = index - 1;
      cell.dataset.columnIndex = String(columnIndex);
      cell.classList.add("grid-column-header");
      const columnName = cell.textContent.trim();
      const dtype = cell.title || "unknown";
      cell.innerHTML = `<span class="grid-letter">${columnLabel(columnIndex)}</span><span class="grid-name">${escapeHtml(columnName)}</span><span class="grid-type">${escapeHtml(dtype)}</span>`;
    });

    Array.from(tbody.rows).forEach((row, rowIndex) => {
      let rowNumber = row.querySelector(".grid-row-number");
      if (!rowNumber) {
        rowNumber = document.createElement("th");
        rowNumber.className = "grid-row-number";
        rowNumber.scope = "row";
        row.prepend(rowNumber);
      }
      rowNumber.textContent = String(rowIndex + 1);
      rowNumber.dataset.rowNumber = String(rowIndex);

      Array.from(row.cells).forEach((cell, cellIndex) => {
        if (cell.classList.contains("grid-row-number")) return;
        const columnIndex = cellIndex - 1;
        const header = headerRow.children[columnIndex + 1];
        cell.classList.add("grid-cell");
        cell.tabIndex = 0;
        cell.dataset.columnIndex = String(columnIndex);
        cell.dataset.rowNumber = String(rowIndex);
        cell.dataset.columnName = header?.querySelector(".grid-name")?.textContent || `Column ${columnIndex + 1}`;
      });
    });
  }

  function escapeHtml(value) {
    const element = document.createElement("div");
    element.textContent = String(value ?? "");
    return element.innerHTML;
  }

  async function copySelectedCell(cell) {
    const value = cell?.textContent ?? "";
    try {
      await navigator.clipboard.writeText(value);
      selection.textContent = `Copied · ${value || "blank"}`;
    } catch {
      selection.textContent = "Clipboard access unavailable";
    }
  }

  function moveSelection(cell, rowDelta, columnDelta) {
    const nextRow = Number(cell.dataset.rowNumber) + rowDelta;
    const nextColumn = Number(cell.dataset.columnIndex) + columnDelta;
    const rows = tbody.rows;
    if (nextRow < 0 || nextRow >= rows.length || nextColumn < 0) return;
    const nextCell = rows[nextRow]?.querySelector(`.grid-cell[data-column-index="${nextColumn}"]`);
    if (!nextCell) return;
    selectCell(nextCell);
    nextCell.focus({ preventScroll: true });
    nextCell.scrollIntoView({ block: "nearest", inline: "nearest" });
  }

  tbody.addEventListener("click", (event) => {
    const cell = event.target.closest(".grid-cell");
    if (cell) selectCell(cell);
  });

  tbody.addEventListener("dblclick", (event) => {
    const cell = event.target.closest(".grid-cell");
    if (cell) copySelectedCell(cell);
  });

  tbody.addEventListener("keydown", (event) => {
    const cell = event.target.closest(".grid-cell");
    if (!cell) return;
    const movement = {
      ArrowUp: [ -1, 0 ],
      ArrowDown: [ 1, 0 ],
      ArrowLeft: [ 0, -1 ],
      ArrowRight: [ 0, 1 ],
    }[event.key];

    if (movement) {
      event.preventDefault();
      moveSelection(cell, movement[0], movement[1]);
    } else if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "c") {
      event.preventDefault();
      copySelectedCell(cell);
    }
  });

  const observer = new MutationObserver(() => decorate());
  observer.observe(tbody, { childList: true });
  decorate();
})();
