    prompt = ( 
                    f""" 
                    please MUST provide the complete response according to the days
                    -MUST Fill the data for each day never miss any 
    Create a detailed meal plan for a {dietary_restrictions} diet with exactly {mealperday} per day for {days} , for the {servings} that is  refers to the number of persons its means you have to generate every meal for the {servings} ,if there is for example two then you have to make it for 2 people.
    - the most important point is:{servings} refers to the number of persons if there is {servings} you have to desgined the meal as it can be consumed by {servings} and each person should get the {total_calories}
- Each meal should follow the structure provided, and you must include a exact accurate  shopping list .
- Ensure that the generated meals take into account the following restrictions:
  - Must avoid these allergies: {allergies}.
  - Must exclude these disliked foods: {dislikes}.
- Generate the meal plan in pure HTML format without any additional information or formatting characters like "\\n" or "\\".
- Use only the following HTML structure for each {days}, you must include the {mealperday} in every single day according to the provided {total_calories}, its means the number of total meals  in per day that is {mealperday}, its nutrition should must be equal to the {total_calories}.
-Please use detail and max content in the instructions












  <div >
    
            <!-- Meal Plan Section -->
      
    <h1>Meal Plan</h1>
    <div class="maindiv">

    <div class="upone">
        {''.join(f'''
         <h2>Day {i+1}</h2>
         <p>[here you tell me that for how many people this meal is?]</p>
        <table class="firsttable">
     
            <thead>
                <tr>
                    <th ><b>Meals</b></th>
                    <th ><b>Ingredients</b></th>
                    <th ><b>Instructions</b></th>
                </tr>
            </thead>
            <tbody>
                <tr >
                    [Repeat this <tr> block for {mealperday} time for each meal, for example if there is {mealperday} then you have to repeat it for that times]
                        
                    <td class="firstcolumn">
                        <!-- Meal Info Section -->
                        <div class="firstcolumndiv">
                            <span class="meal">Meal $1</span>
                            <h3 class="maindish" >[Main Dish Name]</h3>
                            <h4  class="sidedish">[Side Dish Name]</h4>
                        </div>

                        <!-- Time Table -->
                        <table class="timetable">
                            <thead>
                                <tr>
                                    <th >Prep</th>
                                    <th >Cook</th>
                                    <th >Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td >[Prep time]</td>
                                    <td >[Cook time]</td>
                                    <td >[Total time]</td>
                                </tr>
                            </tbody>
                        </table>

                        <!-- Nutrition Table -->
                        <div style="margin-top: 16px;">
                            <h5 >Nutritional Information</h5>
                            <table class="nutritable">
                                <thead>
                                    <tr>
                                        <th ></th>
                                        <th >Main</th>
                                        <th >Side</th>
                                        <th >Total</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td >[Nutrition]</td>
                                        <td >[Value]</td>
                                        <td>[Value]</td>
                                        <td >[Value]</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </td>
                    
                    <!-- Ingredients Column -->
                    <td class="secondcolumn">
                        <div >
                            <h6 >Main Dish Ingredients</h6>
                            [Provide detail ingredients to make that dish]
                            <ol>
                                <li >[Ingredient]</li>
                            </ol>
                        </div>
                        <div >
                            <h6>Side Dish Ingredients</h6>
                            [Provide detail ingredients to make that dish]
                            <ol >
                                <li >[Ingredient]</li>
                            </ol>
                        </div>
                    </td>

                    <!-- Instructions Column -->
                    [main dish and side dish instructions should not be exceeded ]
                    <td class="secondcolumn">
                        <div >
                            <h6 >Main Dish Instructions</h6>
                            [Provide detail Instructions to make that dish as a user who didnot even know cooking can easily make this dish (provide detailed recipes)]
                            <p >[Instructions (detailed recipes, use maximum lines)]</p>
                        </div>
                        <div >
                            <h6>Side Dish Instructions</h6>
                            [Provide detail Instructions to make that dish as a user who didnot even know cooking can easily make this dish (provide detailed recipes)]
                            <p >[Instructions (detailed recipes) ]</p>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>
                '''for i in range(days))}
        </div>


        <!-- Shopping List Section -->
 <h1 >Weekly Shopping List</h1>
 [Plese provide detailed shopping list according to the meals never miss single items ]
[NEVER remove style tag and its content from here]
[only and only use the international units , like kg,g,mg, litters,dozen etc.. NEVER USE quantity like i.e: 4 chicken , always use the international units like kg,g,mg, litters,dozen etc..]

[Must Generate a Complete "Weekly" Shopping List:Please provide a detailed
shopping list for a full week of meals, ensuring it includes all necessary
ingredients for each meal.]

<div class="container22">
[please use both column22 means you have to fill both of one like if the first one is filled then fill the 2nd one]
<div class="column22">
<div class="category22">
  <h5>[items type i.e Vegetables,Fruits,Meat,Seafood etc]</h5>
  <ul>
    <li>
      [items name and weekly quantity(please provide the weekly quantity
      means that one multiply to 7 to get weekly quantity of each i.e if
      in meal we use 1 kg oil then you have to multiply 1 with 7 to get
      weekly quantity [you dont have to show the calculations , just
      show the value of weekly quantity] please use the international
      units that any one can understand )]
    </li>
  </ul>
</div>

<div class="category22">
  <h5>[items type i.e Vegetables,Fruits,Meat,Seafood etc]</h5>
  <ul>
    <li>
      [items name and weekly quantity(please provide the weekly quantity
      means that one multiply to 7 to get weekly quantity of each i.e if
      in meal we use 1 kg oil then you have to multiply 1 with 7 to get
      weekly quantity [you dont have to show the calculations , just
      show the value of weekly quantity] please use the international
      units that any one can understand )]
    </li>
  </ul>
</div>
</div>

<div class="column22">
<div class="category22">
  <h5>[items type i.e Vegetables,Fruits,Meat,Seafood etc]</h5>
  <ul>
    <li>
      [items name and weekly quantity(please provide the weekly quantity
      means that one multiply to 7 to get weekly quantity of each i.e if
      in meal we use 1 kg oil then you have to multiply 1 with 7 to get
      weekly quantity [you dont have to show the calculations , just
      show the value of weekly quantity] please use the international
      units that any one can understand )]
    </li>
  </ul>
</div>

<div class="category22">
  <h5>[items type i.e Vegetables,Fruits,Meat,Seafood etc]</h5>
  <ul>
    <li>
      [items name and weekly quantity(please provide the weekly quantity
      means that one multiply to 7 to get weekly quantity of each i.e if
      in meal we use 1 kg oil then you have to multiply 1 with 7 to get
      weekly quantity [you dont have to show the calculations , just
      show the value of weekly quantity] please use the international
      units that any one can understand )]
    </li>
  </ul>
</div>
</div>
</div>



</div>
</div>
</div>
</div>

    """

        
    )
