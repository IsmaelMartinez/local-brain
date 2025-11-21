// Test file with obvious code smells for integration testing

// SMELL 1: Deeply nested conditionals
function validateUser(user) {
  if (user) {
    if (user.name) {
      if (user.email) {
        if (user.age) {
          if (user.age > 18) {
            if (user.verified) {
              if (user.subscription) {
                if (user.subscription.active) {
                  return true;
                }
              }
            }
          }
        }
      }
    }
  }
  return false;
}

// SMELL 2: God function - doing too many things
function processOrder(order) {
  // Validate order
  if (!order.items || order.items.length === 0) {
    throw new Error("No items");
  }

  // Calculate total
  let total = 0;
  for (let i = 0; i < order.items.length; i++) {
    total += order.items[i].price * order.items[i].quantity;
    if (order.items[i].discount) {
      total -= order.items[i].discount;
    }
  }

  // Apply tax
  total = total * 1.08;

  // Check inventory
  for (let i = 0; i < order.items.length; i++) {
    const item = order.items[i];
    const stock = getStock(item.id);
    if (stock < item.quantity) {
      throw new Error("Insufficient stock");
    }
  }

  // Process payment
  const card = order.payment.card;
  if (!card.number || card.number.length !== 16) {
    throw new Error("Invalid card");
  }

  // Send confirmation email
  const email = order.customer.email;
  sendEmail(email, "Order confirmed", "Your order #" + order.id);

  // Update inventory
  for (let i = 0; i < order.items.length; i++) {
    updateStock(order.items[i].id, -order.items[i].quantity);
  }

  // Log transaction
  logTransaction(order.id, total, new Date());

  return { success: true, total: total };
}

// SMELL 3: Magic numbers
function calculateDiscount(price, customerType) {
  if (customerType === 1) {
    return price * 0.9;
  } else if (customerType === 2) {
    return price * 0.85;
  } else if (customerType === 3) {
    return price * 0.75;
  }
  return price;
}

// SMELL 4: Duplicate code
function getUserByEmail(email) {
  const db = connectDB();
  const query = "SELECT * FROM users WHERE email = ?";
  const result = db.execute(query, [email]);
  db.close();
  return result[0];
}

function getUserById(id) {
  const db = connectDB();
  const query = "SELECT * FROM users WHERE id = ?";
  const result = db.execute(query, [id]);
  db.close();
  return result[0];
}

function getUserByUsername(username) {
  const db = connectDB();
  const query = "SELECT * FROM users WHERE username = ?";
  const result = db.execute(query, [username]);
  db.close();
  return result[0];
}

// SMELL 5: No error handling
function parseUserData(jsonString) {
  const data = JSON.parse(jsonString);
  const user = {
    id: data.user.id,
    name: data.user.profile.name,
    email: data.user.profile.contact.email
  };
  return user;
}
