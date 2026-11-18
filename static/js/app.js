// 侧边栏（移动端）
document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("sidebarToggle");
    const sidebar = document.querySelector(".sidebar");
    if (toggle && sidebar) {
        toggle.addEventListener("click", () => sidebar.classList.toggle("show"));
    }

    // 删除/作废等操作二次确认
    document.querySelectorAll("form[data-confirm]").forEach((form) => {
        form.addEventListener("submit", function (event) {
            if (!window.confirm(form.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });
});

/**
 * 明细行（formset）动态增删。
 * @param {string} prefix formset 前缀，如 items
 */
function addFormsetRow(prefix) {
    const totalInput = document.getElementById("id_" + prefix + "-TOTAL_FORMS");
    const container = document.getElementById(prefix + "-rows");
    const template = document.getElementById(prefix + "-empty-template");
    if (!totalInput || !container || !template) return;

    const index = parseInt(totalInput.value, 10);
    const html = template.innerHTML.replace(/__prefix__/g, index);
    const wrapper = document.createElement("div");
    wrapper.innerHTML = html.trim();
    const row = wrapper.firstElementChild;
    container.appendChild(row);
    totalInput.value = index + 1;
    bindFormsetRow(row, prefix);
}

function removeFormsetRow(button, prefix) {
    const row = button.closest(".formset-row");
    const container = document.getElementById(prefix + "-rows");
    if (!row || !container) return;
    const deleteInput = row.querySelector('input[name$="-DELETE"]');
    const idInput = row.querySelector('input[name$="-id"]');
    if (deleteInput && idInput && idInput.value) {
        // 已保存的明细：标记删除后隐藏
        deleteInput.checked = true;
        row.style.display = "none";
        return;
    }
    if (container.querySelectorAll(".formset-row").length <= 1) {
        window.alert("至少保留一条明细");
        return;
    }
    row.remove();
    const totalInput = document.getElementById("id_" + prefix + "-TOTAL_FORMS");
    if (totalInput) {
        // 保持表单管理器的索引连续：重新编号剩余行
        const rows = container.querySelectorAll(".formset-row");
        rows.forEach((item, idx) => {
            item.querySelectorAll("input, select, textarea").forEach((field) => {
                if (field.name) {
                    field.name = field.name.replace(new RegExp(prefix + "-(\\d+)-"), prefix + "-" + idx + "-");
                }
                if (field.id) {
                    field.id = field.id.replace(new RegExp("id_" + prefix + "-(\\d+)-"), "id_" + prefix + "-" + idx + "-");
                }
            });
        });
        totalInput.value = rows.length;
    }
}

function bindFormsetRow(row, prefix) {
    const select = row.querySelector(".herb-select");
    const priceInput = row.querySelector(".price");
    const batchSelect = row.querySelector(".batch-select");
    if (select && priceInput) {
        select.addEventListener("change", function () {
            // 选择药材后自动带出参考单价（模板中注入 window.HERB_PRICES）
            const option = select.options[select.selectedIndex];
            const price = (option && option.dataset.price)
                || (window.HERB_PRICES && window.HERB_PRICES[select.value]);
            if (price && !priceInput.value) {
                priceInput.value = price;
            }
        });
    }
    if (select && batchSelect) {
        select.addEventListener("change", function () {
            const herbId = select.value;
            Array.from(batchSelect.options).forEach((opt) => {
                if (!opt.value) return;
                opt.hidden = opt.dataset.herb !== herbId;
            });
            batchSelect.value = "";
        });
    }
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".formset-row").forEach((row) => {
        const prefix = row.dataset.prefix || "items";
        bindFormsetRow(row, prefix);
    });
});
