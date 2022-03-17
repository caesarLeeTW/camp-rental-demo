let selectEquipment = null;

function rent(equipment) {
  console.log(equipment);
  selectEquipment = equipment;

  const id = document.querySelector("#rent-form .id")
  id.setAttribute("value", equipment.id)

  const title = document.querySelector("#rent-form .title");
  console.log(title)
  title.textContent = equipment.title + title.textContent;

  const img = document.querySelector("#rent-form img");
  img.src = equipment.image_url;

  const countSelect = document.querySelector("#rent-form select")
  countSelect.innerHTML = null;
  const defaultOption = document.createElement("option");
  defaultOption.innerHTML = "Select";
  countSelect.append(defaultOption);
  for (let i = 1; i <= equipment.remain_count; i++) {
    const option = document.createElement("option");
    option.innerHTML = i;
    option.value = i;
    countSelect.append(option);
  }

  const price = document.querySelector("#rent-form .price span");
  price.innerHTML = equipment.price;
}