/* SirenTracker client-side JS */

document.addEventListener('DOMContentLoaded', function () {
  // Text filter for siren table
  var filterInput = document.getElementById('siren-filter');
  var table = document.getElementById('siren-table');
  if (filterInput && table) {
    filterInput.addEventListener('input', function () {
      var query = this.value.toLowerCase();
      var rows = table.querySelectorAll('tbody tr');
      rows.forEach(function (row) {
        var text = row.textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
      });
    });
  }

  // Status filter buttons
  var statusFilter = document.getElementById('status-filter');
  if (statusFilter && table) {
    statusFilter.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-status]');
      if (!btn) return;
      // Update active state
      statusFilter.querySelectorAll('.btn').forEach(function (b) {
        b.classList.remove('active');
      });
      btn.classList.add('active');
      var status = btn.dataset.status;
      var rows = table.querySelectorAll('tbody tr');
      rows.forEach(function (row) {
        if (status === 'all' || row.dataset.status === status) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });
    });
  }

  // Conditional rotation field on test form
  var sirenSelect = document.querySelector('select[name="siren_id"]');
  var rotationField = document.getElementById('rotation-field');
  if (sirenSelect && rotationField) {
    function toggleRotation() {
      var selected = sirenSelect.options[sirenSelect.selectedIndex];
      var sirenType = selected ? selected.dataset.type : '';
      rotationField.style.display = sirenType === 'ROTATE' ? '' : 'none';
    }
    sirenSelect.addEventListener('change', toggleRotation);
    toggleRotation();
  }

  // Confirm dialogs for destructive actions
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (!confirm(el.dataset.confirm)) {
        e.preventDefault();
      }
    });
  });

  // Row click navigation for siren table
  if (table) {
    table.querySelectorAll('tbody tr').forEach(function (row) {
      row.addEventListener('click', function (e) {
        if (e.target.tagName === 'A') return;
        var link = row.querySelector('a');
        if (link) window.location = link.href;
      });
    });
  }
});
