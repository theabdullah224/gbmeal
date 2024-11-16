import React, { useEffect, useState } from "react";
import downarrow from "./Resource/downarrow.svg";
import useStore from "./Store";
import { jwtDecode } from "jwt-decode";
import { useNavigate } from "react-router-dom";
// Importing React,necessary hooks, and assets for managing state and layout effects
import jsPDF from "jspdf";
import "jspdf-autotable"; // Ensure you have this package installed
import "./card.css"; // Import the CSS file
import Logo from "./Resource/logo2.png";
import "jspdf-autotable"; // Ensure you have this package installed
import "./card.css"; // Import the CSS file

import Loader from "./Resource/spinner.svg";

const parseMealPlanData = (mealPlan) => {
  if (typeof mealPlan !== "string" || mealPlan.trim() === "") {
    return [];
  }

  const result = [];
  const dayRegex = /\d+:/g;
  const daySections = mealPlan.split(dayRegex);
  const dayNumbers = mealPlan.match(dayRegex);

  const boldMealNumber = (text) => {
    return text.replace(/(Meal \d+)/, "$1");
  };

  const numberIngredients = (ingredients) => {
    const sections = ingredients.split("-------------------------");
    return sections
      .map((section) => {
        let count = 1;
        return section
          .split("\n")
          .map((line) => {
            line = line.trim();
            if (line.startsWith("-")) {
              return `${count++}. ${line.substring(1).trim()}`;
            }
            return line;
          })
          .join("\n");
      })
      .join("\n-------------------------\n");
  };

  const processMeal = (meal, index) => {
    const mealNumber = `Meal ${index + 1}`;
    let [mealSection, ingredientsSection, instructionsSection] = meal.split(
      /Ingredients:|Instructions:/
    );

    const mealLines = mealSection.split("\n").filter((line) => line.trim());
    const restructuredMealLines = mealLines.map((line) => {
      if (line.toLowerCase().includes("side dish:")) return "\n" + line;
      if (line.toLowerCase().includes("cooking time:")) return "\n" + line;
      if (line.toLowerCase().includes("nutritional information:"))
        return "\n" + line;
      // if (line.toLowerCase().includes("total:\ncalories")) return "\n" + line;
      if (line.toLowerCase().includes("total:")) return "\n" + line;
      return line;
    });

    // Join the restructured lines and bold the meal number
    const mealData = boldMealNumber(restructuredMealLines.join("\n"));

    const ingredientsLines = ingredientsSection
      ? ingredientsSection.split("\n").filter((line) => line.trim())
      : [];
    const restructuredIngredientsLines = ingredientsLines.map((line) => {
      if (line.toLowerCase().includes("main dish:")) return line; // No newline before Main Dish:
      if (line.toLowerCase().includes("side dish:")) return "\n" + line;
      return line;
    });
    const ingredients = restructuredIngredientsLines.join("\n");

    // Process instructions lines
    const instructionsLines = instructionsSection
      ? instructionsSection.split("\n").filter((line) => line.trim())
      : [];
    const restructuredInstructionLines = instructionsLines.map((line) => {
      if (line.toLowerCase().includes("side dish:")) return "\n" + line;
      return line;
    });
    const instructions = restructuredInstructionLines.join("\n");

    return `${mealData}\n\nIngredients:\n${ingredients}\n\nInstructions:\n${instructions}`;
  };

  for (let i = 1; i < daySections.length; i++) {
    const dayNumber = dayNumbers[i - 1].trim();
    const dayContent = daySections[i].trim();

    const meals = dayContent.split(/Meal \d+/).filter(Boolean);
    const dayRow = [dayNumber];

    meals.forEach((meal, index) => {
      dayRow.push(processMeal(meal, index));
    });

    result.push(dayRow);
  }

  return result;
};

function Pref() {
  const API_BASE_URL = "https://meeel.xyz";
  const navigate = useNavigate();
  const [loader, setLoader] = useState(false);
  const { isLoggedIn, setIsLoggedIn } = useStore();
  const [selectedPreferredMeal, setSelectedPreferredMeal] = useState([]);
  const [selectedFoodAllergies, setSelectedFoodAllergies] = useState([]);
  const [selecteddietaryRestrictions, setSelecteddietaryRestrictions] =
    useState([]);
  const [selecteddislike, setSelecteddislike] = useState([]);
  const [selectedServings, setSelectedServings] = useState("");
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [selectedFamilyMembers, setSelectedFamilyMembers] = useState("1");
  const [isEditable, setIsEditable] = useState(true);
  const [colories, setcolories] = useState("");
  const [servingss, setservingss] = useState("");
  const [familymember, setfamilymember] = useState("1");
  const [allergy, setallergy] = useState("");
  const [dislike, setdislike] = useState("");
  const [diatryrestriction, setdiatryrestriction] = useState("");
  const [Error, setError] = useState("");

  const userdataa = localStorage.getItem("userdata");
  useEffect(() => {
    const user = localStorage.getItem("user");
    if (userdata) {
      const parsedUserData = JSON.parse(userdataa);
      setcolories(parsedUserData.total_calories);
      setdiatryrestriction(parsedUserData.dietary_restriction);
      setfamilymember(parsedUserData.preferred_meal);
      setallergy(parsedUserData.food_allergy);
      setdislike(parsedUserData.dislikes);
      setservingss(parsedUserData.servings);
      
    } else {
    }
    if (user) {
      setIsLoggedIn(true);
      setIsSubscribed(user.isSubscribed || false);
    }
    if (user) {
      setIsLoggedIn(true);
    }

    if (user) {
      setIsLoggedIn(true);
      // Check if the user has already generated a PDF or is subscribed
      const userData = JSON.parse(user);
      // setHasGeneratedPDF(userData.hasGeneratedPDF || false);
      setIsSubscribed(userData.isSubscribed || false);
    }
  }, [servingss, diatryrestriction, familymember, dislike, allergy, colories,userdataa]);

  const userdata = localStorage.getItem("userdata");
  const parsedUserData = JSON.parse(userdata);

  const [menuStates, setMenuStates] = useState({
    servings: { open: false, selected: parsedUserData?.servings  } ,
    allergy: { open: false, selected: parsedUserData?.food_allergy },
    preference: { open: false, selected: parsedUserData?.total_calories },
    dislike: { open: false, selected: parsedUserData?.dislikes },
    mealPlan: { open: false, selected: parsedUserData?.dietary_restriction },
    familyMembers: { open: false, selected: parsedUserData?.preferred_meal },
  });
  const handleInputChange = (menu, value) => {
    setMenuStates({
      ...menuStates,
      [menu]: {
        ...menuStates[menu],
        inputValue: value // Update the input field value
      }
    });
  };
  const renderMenuItem = (menu, title, placeholder, options) => (
    <li className="relative ">
      <span className="text-base font-roboto font-bold">{title}</span>
      <button
        onClick={() => isEditable && handleMenuClick(menu)}
        className={`text-sm text-Text2 border-2 rounded-lg border-[#A6AE9D]  px-4 py-3 w-[75vw] sm:w-[30rem] flex justify-between items-center ${
          !isEditable && "opacity-50 cursor-not-allowed"
        }`}
        disabled={!isEditable}
      >
        {menuStates[menu].selected || placeholder}{" "}
        <span>
          <img src={downarrow} className="w-5 ml-3" alt="" />
        </span>
      </button>
      {menuStates[menu].open && (
        <ul className="absolute z-40 left-0 mt-2 bg-white border border-gray-300 w-full px-2 py-2">
          {title === "Tell us about your food allergy" &&(
           <input
           type="text"
           value={menuStates[menu].inputValue || ""}
           onChange={(e) => handleInputChange(menu, e.target.value)} 
           onBlur={() => handleOptionSelect(menu, menuStates[menu].inputValue)}  // Auto-select on blur (when input loses focus)
           className="w-full border-2 py-2 text-xs sm:text-sm rounded-md sm:rounded-lg px-2"
           placeholder="Tell us about your food allergy"
         />
          )}
          {title === "Tell us about the food you dislike" &&(
           <input
           type="text"
           value={menuStates[menu].inputValue || ""}
           onChange={(e) => handleInputChange(menu, e.target.value)} 
           onBlur={() => handleOptionSelect(menu, menuStates[menu].inputValue)}  // Auto-select on blur (when input loses focus)
           className="w-full border-2 py-2 text-xs sm:text-sm rounded-md sm:rounded-lg px-2"
           placeholder="Tell us about the food you dislike"
         />
          )}
          {options.map((option) => (
            <li key={option}>
              <span
                onClick={() => handleOptionSelect(menu, option)}
                className="block px-4 py-2 hover:bg-gray-300 cursor-pointer"
              >
                {option}
              </span>
            </li>
          ))}
        </ul>
      )}
    </li>
  );

  const dataToSend = {
    servings: menuStates.servings.selected || "",
    food_allergy: menuStates.allergy.selected || "",
    preferred_meal: menuStates.familyMembers.selected || "",
    dislikes: menuStates.dislike.selected || "",
    dietary_restriction: menuStates.mealPlan.selected || "",
    total_calories: menuStates.preference.selected || "",
    // Note: 'members' field is not used in the backend, so we're omitting it
  };
  // console.log(dataToSend)
  // handle update-----------
  const handleSubmit = async () => {
    const user = await localStorage.getItem("user");
    const parsedUser = JSON.parse(user); // Convert string to object
    const userId = parsedUser.user_id;
    // handleEditClick();

    try {
      const dataToSend = {
        servings: menuStates.servings.selected || "",
        food_allergy: menuStates.allergy.selected || "",
        preferred_meal: menuStates.familyMembers.selected || "",
        dislikes: menuStates.dislike.selected || "",
        dietary_restriction: menuStates.mealPlan.selected || "",
        total_calories: menuStates.preference.selected || "",
        // Note: 'members' field is not used in the backend, so we're omitting it
      };

      const response = await fetch("https://meeel.xyz/update", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: userId.toString(), // Use the actual user ID
        },
        body: JSON.stringify(dataToSend),
      });
      const result = await response.json();

      if (response.ok) {
        alert("Update successful");
       

        // setMessage(result.message);
        setError(""); // Clear any previous errors
        
        // Update local state or context with the new values
        // For example:
        // updateUserPreferences(dataToSend);
      } else {
        // setError(result.error || "An error occurred while updating");
        // setMessage(""); // Clear any previous messages
      }
    } catch (err) {
      // console.error("An error occurred:", err.message);
      setError("An error occurred: " + err.message);
    }
  };

  const handleOptionSelect = (menu, option) => {
    setMenuStates((prevState) => ({
      ...prevState,
      [menu]: { open: false, selected: option },
    }));
  };
  const handleMenuClick = (menu) => {
    setMenuStates((prevState) => ({
      ...prevState,
      [menu]: { ...prevState[menu], open: !prevState[menu].open },
    }));
  };
  const handleEditClick = () => {
    setIsEditable((prev) => !prev);
  };
  const validateFields = () => {
    // Check if "servings" and "preference" have been selected
    const isServingsSelected = menuStates.servings.selected !== "";
    const isPreferenceSelected = menuStates.mealPlan.selected !== "";

    // Only return true if both "servings" and "preference" are selected
    return isServingsSelected && isPreferenceSelected;
  };
  const sendDataToBackend = () => {
    const servings = menuStates.servings.selected || ""; // Get selected servings
    const familyMembers = menuStates.familyMembers.selected || "";
    const completeservings = servings;

    const dataToSend = {
      servings: completeservings || "",
      allergy: menuStates.allergy.selected || "",
      preference: menuStates.preference.selected || "",
      dislike: menuStates.dislike.selected || "",
      mealPlan: menuStates.mealPlan.selected || "",
    };
    

    // Send dataToSend to your backend
    // Example: axios.post('/api/endpoint', dataToSend);
  };

  //   generate and send pdf--------------
  const generateAndSendPDF = async (email) => {
    sendDataToBackend();
    setLoader(true);
    const allergy = selectedFoodAllergies;
    const user = await localStorage.getItem("user");
    const parsedUser = JSON.parse(user); // Convert string to object
    const userId = parsedUser.user_id;
    try {
      const generateResponse = await fetch(`${API_BASE_URL}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preferredMeal: menuStates.preference.selected || "nothing",
          servings: menuStates.servings.selected || "2 servings",
          allergies: menuStates.allergy.selected || "nothing",
          dislikes: menuStates.dislike.selected || "nothing",
          dietaryRestrictions: menuStates.mealPlan.selected || "nothing",
          total_calories:menuStates.preference.selected || "blank",
          id:userId
        }),
      });

      const generateData = await generateResponse.json();
    //   const { pdf } = generateData;
  
    //   const pdfBlob = base64ToBlob(pdf, "application/pdf");
     
    
    
    // const pdfUrl = URL.createObjectURL(pdfBlob);
    
    
    // const link = document.createElement("a");
    // link.href = pdfUrl;
    // link.download = "meal_plan.pdf"; 
    
   
    // document.body.appendChild(link);
    // link.click();
    // document.body.removeChild(link);
    
 
    // URL.revokeObjectURL(pdfUrl);
    const mealPlanBlob = base64ToBlob(generateData.meal_plan_pdf, "application/pdf");
    const mealPlanUrl = URL.createObjectURL(mealPlanBlob);
    const mealPlanLink = document.createElement("a");
    mealPlanLink.href = mealPlanUrl;
    mealPlanLink.download = "meal_plan.pdf";
    document.body.appendChild(mealPlanLink);
    mealPlanLink.click();
    document.body.removeChild(mealPlanLink);
    URL.revokeObjectURL(mealPlanUrl);

    // Handle shopping list PDF
    const shoppingListBlob = base64ToBlob(generateData.shopping_list_pdf, "application/pdf");
    const shoppingListUrl = URL.createObjectURL(shoppingListBlob);
    const shoppingListLink = document.createElement("a");
    shoppingListLink.href = shoppingListUrl;
    shoppingListLink.download = "shopping_list.pdf";
    document.body.appendChild(shoppingListLink);
    shoppingListLink.click();
    document.body.removeChild(shoppingListLink);
    URL.revokeObjectURL(shoppingListUrl);
        
     
      if (!generateResponse.ok || generateData.error) {
        throw new Error(generateData.error || "Failed to generate PDF.");
      }

   

      const sendResponse = await fetch(`https://meeel.xyz/send-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          meal_plan_pdf: generateData.meal_plan_pdf,
          shopping_list_pdf: generateData.shopping_list_pdf
      }),
      });
      
    

      const sendData = await sendResponse.json();

      if (!sendResponse.ok || sendData.error) {
        throw new Error(sendData.error || "Failed to send PDF.");
      }

      alert("PDF generated and sent successfully!");
      setSelectedFoodAllergies([]);
      setSelecteddislike([]);
      setSelecteddietaryRestrictions([]);
      setSelectedServings("");
      setSelectedPreferredMeal("");

      setLoader(false);
    } catch (error) {}
  };

  // Add this function to check if the user is logged in
  const checkLoginStatus = () => {
    const token = localStorage.getItem("access_token");
    if (token) {
      const decodedToken = jwtDecode(token);
      const currentTime = Date.now() / 1000;
      if (decodedToken.exp > currentTime) {
        setIsLoggedIn(true);
        // You might want to refresh the token here if it's close to expiring
      } else {
        // Token has expired, log the user out
        // handleLogout();
      }
    }
  };

  const handleGeneratePDF = async () => {
    if (!validateFields()) {
      alert("Please select both Servings and Preferred Meal");
    } else {
      setLoader(true);

      const user = JSON.parse(localStorage.getItem("user"));
      if (!user || !user.email) {
        // console.error("User email not found in localStorage");
        alert("Please log in again.");
        setLoader(false);
        return;
      }

      try {
        const response = await fetch(`${API_BASE_URL}/check-subscription`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: user.email }),
        });
        let attempt = 0;
        if (response.status === 500 && attempt < 3) {
          // Retry logic
          console.warn(`Attempt ${attempt} failed. Retrying...`);
          return await handleGeneratePDF(attempt + 1); // Call itself with an incremented attempt
        }
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.error || "Failed to check subscription status"
          );
        }

        const result = await response.json();

        if (result.isSubscribed && result.canGeneratePDF) {
          setIsSubscribed(true);
          await generateAndSendPDF(user.email);
          setCurrentCardIndex(0);
        } else if (result.isSubscribed && !result.canGeneratePDF) {
          alert(
            "You have already generated a PDF for this subscription period."
          );
        } else {
          navigate("/payment");
        }
      } catch (error) {
        if (error)
          // console.error("Error checking subscription status:", error);
          alert(
            "An error occurred while checking subscription status. Please try again."
          );
      } finally {
        setLoader(false);
      }
    }
  };
  const savePDFToLocalStorage = (pdfData,pdfname) => {
    try {
      const pdfList = JSON.parse(localStorage.getItem("pdfList")) || [];
      const currentDate = new Date();
      
      const newPDF = {
        id: Date.now(),
        name: `${pdfname}.pdf`,
        data: pdfData,
        generatedDate: currentDate.toISOString(),
      };

      // Limit to storing only the last 5 PDFs
      // if (pdfList.length >= 5) {
      // }
      // pdfList.shift(); // Remove the oldest PDF

      pdfList.push(newPDF);
      localStorage.setItem("pdfList", JSON.stringify(pdfList));
    } catch (error) {
      // console.error("Error saving PDF to localStorage:", error);
      // Handle the error (e.g., show a message to the user)
    }
  };
  const generateShoppingList = (mealPlanData) => {
    const doc = new jsPDF();

    // Parse the meal plan data and extract ingredients for both Main Dish and Side Dish
    const ingredientsData = parseMealPlanData(mealPlanData.meal_plan);

    const categorizedIngredients = ingredientsData.flatMap((dayRow) =>
      dayRow.slice(1).flatMap((meal) => {
        const ingredientsSection = meal.match(
          /Ingredients:\n([\s\S]*?)(?=\n\nInstructions:|$)/
        );
        const ingredients = ingredientsSection
          ? ingredientsSection[1].trim().split("\n")
          : [];

        let currentCategory = "mainDish";
        const mainDishIngredients = [];
        const sideDishIngredients = [];

        // Categorize ingredients as Main Dish or Side Dish
        ingredients.forEach((ingredient) => {
          if (ingredient.toLowerCase().includes("main dish:")) {
            currentCategory = "mainDish";
          } else if (ingredient.toLowerCase().includes("side dish:")) {
            currentCategory = "sideDish";
          } else if (ingredient.trim() !== "") {
            if (currentCategory === "mainDish") {
              mainDishIngredients.push(ingredient.trim());
            } else {
              sideDishIngredients.push(ingredient.trim());
            }
          }
        });

        return {
          mainDish: mainDishIngredients,
          sideDish: sideDishIngredients,
        };
      })
    );

    // Function to clean up and format ingredients
    const formatIngredients = (ingredients) => {
      return ingredients
        .map((item) => {
          // Remove any existing numbering at the start
          const cleanItem = item.replace(/^\d+\.\s*/, "").trim();
          return cleanItem;
        })
        .filter((item, index, self) => self.indexOf(item) === index) // Remove duplicates
        .map((item, index) => `${index + 1}. ${item}`) // Add clean numbering
        .join("\n");
    };

    // Combine all main dish and side dish ingredients
    const allMainDishIngredients = categorizedIngredients.flatMap(
      (cat) => cat.mainDish
    );
    const allSideDishIngredients = categorizedIngredients.flatMap(
      (cat) => cat.sideDish
    );

    // Format the ingredients
    const formattedMainDish = formatIngredients(allMainDishIngredients);
    const formattedSideDish = formatIngredients(allSideDishIngredients);

    // Structure the table body (now just one row with two cells)
    const tableBody = [[formattedMainDish, formattedSideDish]];

    doc.setFontSize(20);
    doc.text("Shopping List", 105, 18, null, null, "center");
    doc.addImage(Logo, "PNG", 160, 8, 40, 10);

    // Define the column headers for the table
    const headers = [["Main Dish", "Side Dish"]];

    // Create the table with two columns (Main Dish and Side Dish)
    doc.autoTable({
      head: headers,
      body: tableBody,
      startY: 25,
      theme: "grid",
      headStyles: {
        fillColor: [115, 128, 101],
        textColor: [255, 255, 255],
        fontSize: 12,
        fontStyle: "bold",
        valign: "middle",
        halign: "center",
      },
      columnStyles: {
        0: { cellWidth: (doc.internal.pageSize.width - 40) / 2 }, // Main Dish column
        1: { cellWidth: (doc.internal.pageSize.width - 40) / 2 }, // Side Dish column
      },
      styles: {
        fontSize: 10,
        cellPadding: 5,
      },
      didParseCell: function (data) {
        if (data.section === "body") {
          data.cell.styles.cellPadding = 2;
          data.cell.styles.valign = "top";
        }
      },
    });

    // Save and return the PDF
    doc.setFontSize(10);
    doc.text(``, 14, doc.lastAutoTable.finalY + 10);

    const pdfData = doc.output("datauristring");
    savePDFToLocalStorage(pdfData,"ShoppingList");
    doc.save("ShoppingList.pdf");
    return pdfData;
  };

 
 
  // const generatePDF = async (htmlData, logoUrl = null) => {
  //   try {
  //     // Initialize PDF document
  //     const pdf = new jsPDF({
  //       unit: 'pt',
  //       format: 'a4',
  //       orientation: 'portrait'
  //     });
  
  //     // Define constants
  //     const pageWidth = pdf.internal.pageSize.getWidth();
  //     const pageHeight = pdf.internal.pageSize.getHeight();
  //     const margin = {
  //       top: 40,
  //       right: 40,
  //       bottom: 40,
  //       left: 40
  //     };
  
  //     let yOffset = margin.top;
  
  //     // Custom colors
  //     const colors = {
  //       headerBg: [116, 128, 98],    // #748062
  //       textDark: [51, 51, 51],      // #333333
  //       textLight: [255, 255, 255],  // #FFFFFF
  //       borderColor: [163, 163, 163],// #a3a3a3
  //       bgLight: [249, 249, 249]     // #f9f9f9
  //     };
  
  //     // Add logo if provided
  //     if (logoUrl) {
  //       try {
  //         const logoImg = new Image();
  //         logoImg.src = logoUrl;
  //         await new Promise((resolve, reject) => {
  //           logoImg.onload = resolve;
  //           logoImg.onerror = reject;
  //         });
  
  //         const maxLogoWidth = 150;
  //         let logoWidth = logoImg.width;
  //         let logoHeight = logoImg.height;
          
  //         if (logoWidth > maxLogoWidth) {
  //           const ratio = maxLogoWidth / logoWidth;
  //           logoWidth = maxLogoWidth;
  //           logoHeight *= ratio;
  //         }
  
  //         const logoX = (pageWidth - logoWidth) / 2;
  //         pdf.addImage(logoImg, 'PNG', logoX, yOffset, logoWidth, logoHeight);
  //         yOffset += logoHeight + 30;
  //       } catch (error) {
  //         console.error('Error adding logo:', error);
  //       }
  //     }
  
  //     // Helper function to draw table header
  //     const drawTableHeader = (headers, startY, columnWidths) => {
  //       let x = margin.left;
  //       pdf.setFillColor(...colors.headerBg);
  //       pdf.setTextColor(...colors.textLight);
  //       pdf.setFont('helvetica', 'bold');
  //       pdf.setFontSize(10);
  
  //       headers.forEach((header, index) => {
  //         // Add validation for rect parameters
  //         if (isNaN(x) || isNaN(startY) || isNaN(columnWidths[index]) || 
  //             x === null || startY === null || columnWidths[index] === null) {
  //           throw new Error('Invalid parameters for rectangle drawing');
  //         }
  
  //         pdf.rect(x, startY, columnWidths[index], 30, 'F');
  //         pdf.rect(x, startY, columnWidths[index], 30, 'S');
          
  //         const text = header.toUpperCase();
  //         const textWidth = pdf.getStringUnitWidth(text) * 10;
  //         const textX = x + (columnWidths[index] - textWidth) / 2;
  //         pdf.text(text, textX, startY + 20);
          
  //         x += columnWidths[index];
  //       });
  
  //       return startY + 30;
  //     };
  
  //     // Helper function to draw cell with wrapped text
  //     const drawCell = (text, x, y, width, height) => {
  //       const words = text.split(' ');
  //       let line = '';
  //       let lineHeight = 12;
  //       let currentY = y + 15;
  
  //       pdf.setFontSize(10);
  //       words.forEach(word => {
  //         const testLine = line + (line ? ' ' : '') + word;
  //         const testWidth = pdf.getStringUnitWidth(testLine) * 10;
          
  //         if (testWidth > width - 20 && line !== '') {
  //           pdf.text(line, x + 10, currentY);
  //           line = word;
  //           currentY += lineHeight;
  //         } else {
  //           line = testLine;
  //         }
  //       });
        
  //       if (line !== '') {
  //         pdf.text(line, x + 10, currentY);
  //       }
  
  //       return Math.max(height, currentY - y + lineHeight);
  //     };
  
  //     // Process main meal table
  //     const processMealTable = () => {
  //       const columnWidths = [
  //         (pageWidth - margin.left - margin.right) / 3,
  //         (pageWidth - margin.left - margin.right) / 3,
  //         (pageWidth - margin.left - margin.right) / 3
  //       ];
  
  //       // Draw main table header
  //       yOffset = drawTableHeader(['Meals', 'Ingredients', 'Instructions'], yOffset, columnWidths);
  
  //       // Parse the HTML content
  //       const parser = new DOMParser();
  //       const doc = parser.parseFromString(htmlData, 'text/html');
  //       const mealRows = doc.querySelectorAll('table:first-of-type tbody tr');
  
  //       mealRows.forEach(row => {
  //         const cells = row.querySelectorAll('td');
  //         let maxHeight = 0;
  //         let rowHeight = 200; // Default row height
  
  //         // Calculate required height based on content
  //         cells.forEach((cell, index) => {
  //           const cellContent = cell.textContent.trim();
  //           const lines = Math.ceil(cellContent.length / 40); // Rough estimate
  //           const estimatedHeight = lines * 15; // 15pt per line
  //           rowHeight = Math.max(rowHeight, estimatedHeight);
  //         });
  
  //         // Process each cell
  //         cells.forEach((cell, index) => {
  //           const x = margin.left + (columnWidths[index] * index);
            
  //           // Validate parameters before drawing rectangle
  //           if (isNaN(x) || isNaN(yOffset) || isNaN(columnWidths[index]) || isNaN(rowHeight)) {
  //             console.error('Invalid rectangle parameters:', { x, y: yOffset, width: columnWidths[index], height: rowHeight });
  //             return;
  //           }
  
  //           pdf.setFillColor(...colors.bgLight);
  //           pdf.rect(x, yOffset, columnWidths[index], rowHeight, 'F');
  
  //           pdf.setTextColor(...colors.textDark);
  //           pdf.setFont('helvetica', 'normal');
  
  //           const cellHeight = drawCell(
  //             cell.textContent.trim(),
  //             x,
  //             yOffset,
  //             columnWidths[index],
  //             rowHeight
  //           );
  
  //           maxHeight = Math.max(maxHeight, cellHeight);
  //         });
  
  //         yOffset += maxHeight;
  //       });
  
  //       // Add some spacing
  //       yOffset += 30;
  //     };
  
  //     // Process grocery list table
  //     const processGroceryTable = () => {
  //       // Check if new page needed
  //       if (yOffset + 400 > pageHeight) {
  //         pdf.addPage();
  //         yOffset = margin.top;
  //       }
  
  //       const columnWidths = [
  //         (pageWidth - margin.left - margin.right) * 0.3,
  //         (pageWidth - margin.left - margin.right) * 0.7
  //       ];
  
  //       // Draw grocery table header
  //       yOffset = drawTableHeader(['Meal', 'Grocery Items to Purchase'], yOffset, columnWidths);
  
  //       // Parse grocery table
  //       const parser = new DOMParser();
  //       const doc = parser.parseFromString(htmlData, 'text/html');
  //       const groceryRows = doc.querySelectorAll('table:last-of-type tbody tr');
  
  //       groceryRows.forEach(row => {
  //         const cells = row.querySelectorAll('td');
  //         let maxHeight = 0;
  //         let rowHeight = 150; // Default row height
  
  //         // Calculate required height based on content
  //         cells.forEach((cell, index) => {
  //           const cellContent = cell.textContent.trim();
  //           const lines = Math.ceil(cellContent.length / 40); // Rough estimate
  //           const estimatedHeight = lines * 15; // 15pt per line
  //           rowHeight = Math.max(rowHeight, estimatedHeight);
  //         });
  
  //         cells.forEach((cell, index) => {
  //           const x = margin.left + (columnWidths[index] * index);
            
  //           // Validate parameters before drawing rectangle
  //           if (isNaN(x) || isNaN(yOffset) || isNaN(columnWidths[index]) || isNaN(rowHeight)) {
  //             console.error('Invalid rectangle parameters:', { x, y: yOffset, width: columnWidths[index], height: rowHeight });
  //             return;
  //           }
  
  //           pdf.setFillColor(...colors.bgLight);
  //           pdf.rect(x, yOffset, columnWidths[index], rowHeight, 'F');
  
  //           pdf.setTextColor(...colors.textDark);
  //           pdf.setFont('helvetica', 'normal');
  
  //           const cellHeight = drawCell(
  //             cell.textContent.trim(),
  //             x,
  //             yOffset,
  //             columnWidths[index],
  //             rowHeight
  //           );
  
  //           maxHeight = Math.max(maxHeight, cellHeight);
  //         });
  
  //         yOffset += maxHeight;
  //       });
  //     };
  
  //     // Generate the PDF content
  //     processMealTable();
  //     processGroceryTable();
  
  //     // Add page numbers
  //     const totalPages = pdf.internal.getNumberOfPages();
  //     for (let i = 1; i <= totalPages; i++) {
  //       pdf.setPage(i);
  //       pdf.setFontSize(9);
  //       pdf.setTextColor(128, 128, 128);
  //       pdf.text(
  //         `Page ${i} of ${totalPages}`,
  //         pageWidth - margin.right - 60,
  //         pageHeight - margin.bottom / 2
  //       );
  //     }
  
  //     // Save the PDF
  //     pdf.save('meal-plan.pdf');
  //     console.log('Meal Plan PDF generated successfully');
  
  //   } catch (error) {
  //     console.error('Error generating meal plan PDF:', error);
  //     throw error;
  //   }
  // };

  function base64ToBlob(base64, type) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Uint8Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    return new Blob([byteNumbers], { type });
}
  return (
    <div>
      <div className="">
        <div className="max-w-[40rem]  my-[2rem] sm:my-[5rem] xl:px-14 mx-auto">
          <div className="m-auto xl:m-0  w-fit flex flex-col xl:items-start items-center ">
            {/* <h2 className="text-2xl text-center xl:text-left mb-5 inline-block text-Text1 border-b-8 border-S-Orange leading-none font-bold">
              Preferences
            </h2>
            <p className="text-lg text-center xl:text-left mb-5 w-[30rem] xl:w-[50rem] text-Text2 px-4 sm:px-0">
              Preferences play a crucial role in crafting a personalized meal
              plan. Your input allows us to tailor options that align with your
              tastes and dietary needs, ensuring a satisfying experience while
              promoting your health goals.
            </p> */}
          </div>

          <div className=" flex  flex-col justify-center items-center xl:justify-start xl:items-start">
            <ul className="w-full gap-4 flex flex-col xl:flex-row items-center xl:flex-wrap">
              {renderMenuItem(
                "servings",
                "How many servings are required",
                `${menuStates.servings.selected || "Select servings"}`,
                ["1 serving", "2 servings", "3 servings", "4 servings",]
              )}
              {renderMenuItem(
                "allergy",
                "Tell us about your food allergy",
                menuStates.allergy.selected ||
                  "Enter/select allergy if you have any",
                  
                [
                  "Peanuts",
                  "Gluten",
                  "Dairy",
                  "Shell fish",
                  "Eggs",
                  "Cheese",
                  "Tofu",
                  "Butter",
                  "Coconut",
                ]
              )}
              {renderMenuItem(
                "dislike",
                "Tell us about the food you dislike",
                menuStates.dislike.selected || "Enter/select food dislikes",
                ["Fish", "Mushrooms", "Chicken", "Pork", "Beef"]
              )}
              {renderMenuItem(
                "mealPlan",
                "Choose your preferred meal plan",
                menuStates.mealPlan.selected ||
                  "select preferred meal plan",
                [
                  "Carb (promotes weight loss)",
                  "Balanced diet ( Mediterranean diet)",
                  "Carnivore diet",
                  "Paleo diet",
                  "Vegetarian",
                ]
              )}
              {/* {renderMenuItem(
                "familyMembers",
                "Choose your Family Members",
                menuStates.familyMembers.selected ||
                  "Enter/select Family Members",
                [
                  "1",
                  "2",
                  "3",
                  "4",
                  "5",
                  "6",
                  "7",
                  "8",
                  "9",
                  "10",
                  "11",
                  "12",
                  "13",
                  "14",
                  "15",
                  "16",
                  "17",
                  "18",
                  "19",
                ]
              )} */}
              {renderMenuItem(
                "preference",
                "Choose Your Preferred Calories",
                menuStates.preference.selected ||
                  "Enter/select preferred Calories",
                [
                  "Low (Under 1,500 calories)",
                  "Moderate (1,500 - 2,500 calories)",
                  "High (2,500 - 3,500 calories)",
                  "Very High (3,500+ calories)",
                ]
              )}
            </ul>

            <div className="flex gap-2 flex-col sm:flex-row sm:gap-2 flex-wrap items-center justify-center">

            <button
              onClick={handleGeneratePDF}
              className={`${
                loader && "disabled:opacity-50 cursor-not-allowed"
                } mt-4    py-2 px-6 box-border rounded-lg flex items-center justify-center bg-P-Green1 text-white shadow-[inset_4px_4px_8px_#2a322179] hover:shadow-[inset_0px_0px_0px_#2A3221] font-roboto font-medium text-base`}
              disabled={loader}
            >
              {loader ? "Generating..." : "Generate PDF"}
            </button>
            {isEditable ? (
              <button
              onClick={handleSubmit}
              className="sm:mt-4   py-2 px-14 box-border rounded-lg flex items-center justify-center bg-P-Green1 text-white shadow-[inset_4px_4px_8px_#2a322179] hover:shadow-[inset_0px_0px_0px_#2A3221] font-roboto font-medium text-base"
              >
                save
              </button>
            ) : (
              <button
              onClick={handleEditClick}
              className="sm:mt-4   py-2 px-14 box-border rounded-lg flex items-center justify-center bg-P-Green1 text-white shadow-[inset_4px_4px_8px_#2a322179] hover:shadow-[inset_0px_0px_0px_#2A3221] font-roboto font-medium text-base"
              >
                Edit
              </button>
            )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Pref;
