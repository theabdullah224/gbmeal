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
    allergy: { open: false, selected: parsedUserData?.food_allergy.replace(/[{}"]/g, '')  || [], inputValue: '' },
    preference: { open: false, selected: parsedUserData?.total_calories },
    dislike: { open: false, selected: parsedUserData?.dislikes.replace(/[{}"]/g, '') ||  [], inputValue: ''},
    mealPlan: { open: false, selected: parsedUserData?.dietary_restriction },
    familyMembers: { open: false, selected: parsedUserData?.preferred_meal },
    days: { open: false, selected: parsedUserData?.days },
    MealPerDay: { open: false, selected: parsedUserData?.mealperday },
  });


  console.log(parsedUserData?.mealperday)

  const handleInputChange = (menu, value) => {
    setMenuStates({
      ...menuStates,
      [menu]: {
        ...menuStates[menu],
        inputValue: value // Update the input field value
      }
    });
  };
  const handleInputKeyDown = (menu, e) => {
    if (e.key === 'Enter' && e.target.value.trim()) {
      e.preventDefault();
      addCustomOption(menu, e.target.value.trim());
    }
  };

  const addCustomOption = (menu, value) => {
    if (!value) return;
    
    setMenuStates(prev => {
      const currentSelected = Array.isArray(prev[menu].selected) ? prev[menu].selected : [];
      if (!currentSelected.includes(value)) {
        return {
          ...prev,
          [menu]: {
            ...prev[menu],
            selected: [...currentSelected, value],
            inputValue: ''
          }
        };
      }
      return prev;
    });
  };

  const handleOptionSelect = (menu, option) => {
    if (menu === 'allergy' || menu === 'dislike') {
      setMenuStates(prev => {
        const currentSelected = Array.isArray(prev[menu].selected) ? prev[menu].selected : [];
        const updatedSelected = currentSelected.includes(option)
          ? currentSelected.filter(item => item !== option)
          : [...currentSelected, option];
        
        return {
          ...prev,
          [menu]: {
            ...prev[menu],
            selected: updatedSelected,
            open: true // Keep the menu open for multi-select
          }
        };
      });
    } else {
      // Original single-select behavior for other menus
      setMenuStates((prevState) => ({
        ...prevState,
        [menu]: { open: false, selected: option },
      }));
    }
  };

 

  const renderMenuItem = (menu, title, placeholder, options) => (
    <li className="relative">
      <span className="text-base font-roboto font-bold truncate">{title}</span>
      <button
        onClick={() => isEditable && handleMenuClick(menu)}
        className={`text-sm text-Text2 border-2 rounded-lg border-[#A6AE9D] px-4 py-3 w-[75vw] sm:w-[30rem] flex justify-between items-center truncate  ${
          !isEditable && "opacity-50 cursor-not-allowed"
        }`}
        disabled={!isEditable}
      >
        {(menu === 'allergy' || menu === 'dislike') && Array.isArray(menuStates[menu].selected) 
          ? menuStates[menu].selected.join(', ')
          : menuStates[menu].selected || placeholder}
        <span>
          <img src={downarrow} className="w-5 ml-3" alt="" />
        </span>
      </button>
      {menuStates[menu].open && (
        <ul className="absolute z-40 left-0 mt-2 bg-white border border-gray-300 w-full px-2 py-2">
          {(title === "Tell us about your food allergy" || title === "Tell us about the food you dislike") && (
            <input
              type="text"
              value={menuStates[menu].inputValue || ""}
              onChange={(e) => handleInputChange(menu, e.target.value)}
              onKeyDown={(e) => handleInputKeyDown(menu, e)}
              className="w-full border-2 py-2 text-xs sm:text-sm rounded-md sm:rounded-lg px-2 mb-2"
              placeholder={`Type and press Enter to add custom ${menu === 'allergy' ? 'allergy' : 'dislike'}`}
            />
          )}
          
          {options.map((option) => (
            <li key={option}>
              {(title === "Tell us about your food allergy" || title === "Tell us about the food you dislike") ? (
                <div className="flex items-center px-4 py-2 hover:bg-gray-100 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={Array.isArray(menuStates[menu].selected) && menuStates[menu].selected.includes(option)}
                    onChange={() => handleOptionSelect(menu, option)}
                    className="mr-2"
                  />
                  <span onClick={() => handleOptionSelect(menu, option)}>
                    {option}
                  </span>
                </div>
              ) : (
                <span
                  onClick={() => handleOptionSelect(menu, option)}
                  className="block px-4 py-2 hover:bg-gray-300 cursor-pointer"
                >
                  {option}
                </span>
              )}
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
        days:menuStates.days.selected || "",
        mealperday:menuStates.MealPerDay.selected || ""
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

  // const handleOptionSelect = (menu, option) => {
  //   setMenuStates((prevState) => ({
  //     ...prevState,
  //     [menu]: { open: false, selected: option },
  //   }));
  // };
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
         
          servings: menuStates.servings.selected || "2 servings",
          allergies: menuStates.allergy.selected || "nothing",
          dislikes: menuStates.dislike.selected || "nothing",
          dietaryRestrictions: menuStates.mealPlan.selected || "nothing",
          total_calories:menuStates.preference.selected || "blank",
          mealperday:menuStates.MealPerDay.selected || "blank",
          days:"6 days",
          id:userId
        }),
      });

      const generateData = await generateResponse.json();
    
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
                "MealPerDay",
                "How many Meals are required per Day?",
                `${menuStates.MealPerDay.selected  || "Select Meal/day"}`,
                [ "2 Meals", "3 Meals","4 Meals","5 Meals"]
              )}
             
              {renderMenuItem(
                "servings",
                "How Many Servings Do You Need?",
                `${menuStates.servings.selected || "Select the number of servings you need per meal."}`,
                ["1 Person", "2 People", "3 People", "4 People",]
              )}
              {renderMenuItem(
                "allergy",
                "Tell us about your food allergy",
                menuStates.allergy.selected ||
                  "Enter/select allergy if you have any",
                  
                [                  
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
