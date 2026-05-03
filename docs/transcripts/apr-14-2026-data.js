// Fixes: 3 roll call name-readings + 1 additional misattribution corrected + 5 speaker corrections + 1 text split fixed + 14 additional corrections
const TRANSCRIPT_TURNS = [
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 160,
    "end": 263890,
    "text": "Sa. Sam. Good evening. I would like to call the regular meeting of April 14, 2026 to order. It's good to see the chamber full. We have a lot of things to celebrate tonight. If you are able and so choose, please rise for the Pledge of Allegiance. I pledge allegiance to the flag of the United States of America and to the one nation under God, indivisible, with liberty and justice for all. I will now ask Suzanne Levy, Eric Carzon and Alana Quarles with the City of Fairfax Library to come down for the proclamation acknowledging National Library Week. Well, you'll be in the middle. Okay, I'll be. I'll be in the middle. That sounds reasonable. All right. Whereas Libraries spark creativity, fuel imagination, and inspire lifelong learning, offering a space where individuals of all ages can find joy through exploration and discovery. And whereas. Libraries serve as vibrant community hubs, connecting people with knowledge, technology and resources while fostering civic engagement, critical thinking and cultural enrichment. And whereas. Libraries provide free and equitable access to books, digital tools and innovative programming, ensuring that all individuals, regardless of background, have the support they need to learn, connect, and thrive. And whereas. Libraries partner with schools, businesses and organizations, connecting the dots to maximize resources, increasing efficiency and expand access to essential services, strengthening the entire community. And whereas. Libraries empower job seekers, entrepreneurs and lifelong learners by providing access to resources, training, and opportunities that support career growth and economic success. And whereas. Libraries nurture young minds through story times, STEAM programs and literacy initiatives, fostering curiosity and a love of learning that lasts a lifetime. And whereas. Libraries protect the right to read, think and explore without censorship, standing as champions of intellectual freedom and free expression. And whereas. Dedicated librarians and library workers provide welcoming spaces that inspire discovery, collaboration and creativity for all. And whereas libraries, librarians and library workers across the country are joining together to celebrate National Library Week under the theme, find your joy now. Therefore, I, Catherine S. Reed, Mayor of the City of Fairfax, do hereby proclaim April 19th to the 25th, 2026, as National Library Week in the City of Fairfax and encourage the community during this week to visit their library, explore its resources, and celebrate all the ways that the library helps our community find joy. And with that, I turn it over to Ms. Suzanne Levy."
  },
  {
    "speaker": "Group",
    "speaker_source": "correction",
    "speaker_source_detail": "Brief unidentifiable utterance - labeled REDACTED in error",
    "start": 160,
    "end": 263890,
    "text": "[duplicate segment - superseded by extended preceding turn]"
  },
  {
    "speaker": "Suzanne Levy",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 263890,
    "end": 358580,
    "text": "Okay, thank you, Mayor. I'm honored to be your representative to the Fairfax County Public Library Board of Trustees. I'm in my second year as chairman of the board. Fortunately, you can only serve two years, so I'll be turning it over to somebody in July. But it's a real honor, and some of you may know my career was at the Fairfax City Regional Library. And so this is just a continuation of what I did for many years, and I wanted to introduce our library director, Eric Carzon. Elena Quarles is the branch manager at City of Fairfax, and Jackie Consalvo is the head of the circulation department. So when you go into the library next week to celebrate National Library Week, please say hi to everybody. And if you don't have a library card, we have beautiful new cards that were designed by citizens in the community. And you can replace your old card with a pretty new one, or you can get a card for the first time. We really want to have you coming in our doors, seeing all the wonderful things that are going on. And check out our book sale. The children's book sale is the first weekend in May, and the adult book sale is in the second week of May. And our wonderful friends of the library raised money to support library activities and help us purchase materials that are not in the budget to be purchased. So thank you for this honor. We really appreciate the opportunity to be here."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 358820,
    "end": 373010,
    "text": "Thank you. So now we're going to get a picture, right? And really, if you don't have a library card, really, it's time to get one. You don't have a library. Come on in."
  },
  {
    "speaker": "Suzanne Levy",
    "speaker_source": "correction",
    "speaker_source_detail": "Corrected from Library Staff Member",
    "start": 373250,
    "end": 376450,
    "text": "Well, Mayor Reed has the name to have a library card."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 376930,
    "end": 378930,
    "text": "We expect her to go this way."
  },
  {
    "speaker": "Group",
    "text": "The group is gathering for a group photo."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 379250,
    "end": 380090,
    "text": "You want to go this way?"
  },
  {
    "speaker": "Group",
    "text": "The group is gathering for a group photo."
  },
  {
    "speaker": "Group",
    "text": "The group is gathering for a group photo."
  },
  {
    "speaker": "Group",
    "text": "The group is gathering for a group photo."
  },
  {
    "speaker": "Group",
    "text": "The group is gathering for a group photo."
  },
  {
    "speaker": "Group",
    "text": "The group is gathering for a group photo."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "text": "Okay, good. Oh, you. Okay?"
  },
  {
    "speaker": "Suzanne Levy",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 401410,
    "end": 408010,
    "text": "Thank you so much, and thank you for this. And the staff is going to take it back to the library and put it in a prominent place. I will see you at the library."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 408010,
    "end": 443680,
    "text": "Thank you so much. I'm now going to ask Stephanie Kupka, Anna Safford, City Environmental Sustainability Committee members, Faisa Alam, Rusty Russell, and everyone else who is here from the ESC to come come down here so we can talk about Earth Day and Arbor Day. All right, all right, all right. Did we plan this?"
  },
  {
    "speaker": "Group",
    "text": "[Cross-talk in the room.]"
  },
  {
    "speaker": "Group",
    "text": "[Cross-talk in the room.]"
  },
  {
    "speaker": "Group",
    "text": "[Cross-talk in the room.]"
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 447450,
    "end": 572300,
    "text": "There you go. Monarch butterfly. Later. Okay, not that I want to have any spoilers here, but whereas the City of Fairfax recognizes the natural environment as the foundation of a healthy society and a robust economy, providing essential resources that sustain life and contribute to the well being of all. And whereas the global community faces extraordinary environmental challenges, including environmental degradation, global health issues, loss of habitat, climate change, and water and energy crises. And whereas Earth Day and Arbor Day serve as annual reminders that we are all caretakers of our planet and have an obligation to engage in environmental activism, stewardship commitments, and sustainability efforts to preserve the Earth's. Beauty and resources for current and future generations. And whereas the first Earth Day was celebrated in 1970, calling upon millions of Americans to act for a cleaner, safer and healthier environment and Whereas the City of Fairfax has been recognized nationally as a Tree City USA by the Arbor Day foundation for 40 years, setting aside a special day each year for the planting and celebration of trees is vital to our quality of life and environmental health. And Whereas Earth Day and Arbor Day provide opportunities for the community to come together and participate in activities that promote a cleaner, healthier and more sustainable environment. Now, therefore, I, Catherine S. Reed, Mayor of the City of Fairfax, do hereby proclaim April 22, 2026 as Earth Day and April 24, 2026 as Arbor Day in the City of Fairfax, and hereby encourage our community and businesses to observe these days by taking action to protect and enhance our environment. This includes participating in activities such as planting trees, reducing waste, recycling, picking up litter, conserving energy and clean water, and otherwise engaging in actions big and small to preserve our natural resources for the benefit of all living things. And with that, I will turn it over to Faisa Alam. Is this you? I think so."
  },
  {
    "speaker": "Faisa Alam",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 575020,
    "end": 589740,
    "text": "Good evening, everyone. So I'm here as a science teacher, standing here in front of you and the SC Committee member to kind of this is a great day for all of us. We all are here. We breathe oxygen and we all breathe it thanks to our trees."
  },
  {
    "speaker": "Faisa Alam",
    "speaker_source": "correction",
    "speaker_source_detail": "Corrected from Mayor Catherine Read",
    "start": 590480,
    "end": 651300,
    "text": "So please join us on the Arbor day event on April 25th. And I would also like to make a pitch for making our carbon footprint a little better than what we do. I am one of the persons who benefited from the city's Solarize Virginia program last year, and I have solar panels on my house and few other friends who are also in this room have that. And since October, I have not paid anything to dominion other than $7 something, and I have exported a lot of power out there. So this year, again, the Solarize Virginia is a great program. It's opening up again in April 16th. Stephanie? Yes. 15th. And it will continue. It is a very good vetted program. It's the best rate you're going to get. So just spread the word out and do that. And please join us on the Arbor Day on April 25. The event begins at 9am we will have some students who are written beautiful poetries. They will be reciting. We'll have tree giveaways, tree plantations, and a lot of fun. So please join us."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "correction",
    "speaker_source_detail": "Corrected from Councilmember Tom Peterson",
    "start": 651700,
    "end": 665300,
    "text": "All right, any other remarks? Okay. And I think that's at Pat Rodeo Park. Yes, Pat Rodeo Park. I think that's a new venue for us. Okay, picture"
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 667140,
    "end": 667780,
    "text": "squeeze."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 695640,
    "end": 828040,
    "text": "All right, so joining Stephanie and Anna, I'm looking for Janet Jaworski, Mary Driver Downs Faza Alam and Rusty Russell. You guys, where'd you go? All right, More. More things to celebrate. So many things. Whereas the monarch butterfly is an iconic North American species whose multi generational migration and metamorphosis from caterpillar to butterfly has captured the imagination of millions of Americans. And whereas both the western and eastern monarch populations have seen significant declines with less than 1% of the Western monarch population remaining, while the eastern population has fallen by as much as 90%. And whereas the city of Fairfax recognizes that human health ultimately depends on well functioning ecosystems and that biodiverse regions can better support food production, healthy soil and air quality, and can foster healthy connections between humans and wildlife. And whereas cities, towns and counties have a critical role to play in helping save the monarch butterfly by providing habitat at public parks, in median strips, community gardens, and municipal buildings that serve as community hubs, such as recreation centers, libraries and schools. And whereas simple changes in landscaping ordinances or school policies can make a big difference for the monarch, educating citizens about how to provide essential habitat for monarchs and where and how to grow milkweed, which is a key piece of the puzzle in creating habitat and educating citizens, benefits other pollinators that need healthy habitats as well. Now, therefore, I, Catherine S. Reed, Mayor of the City of Fairfax, do hereby commit to the Mayor's Monarch Pledge. This is a nationwide thing, the Mayor's Monar Monarch Pledge, and encourage all residents to participate in community activities that support and celebrate monarch conservation so that these magnificent butterflies will once again flourish across this continent. And with that, I will turn it over to Ms. Janet Jaworski."
  },
  {
    "speaker": "Janet Jaworski",
    "speaker_source": "correction",
    "speaker_source_detail": "Corrected from Councilmember Anthony Amos",
    "start": 829960,
    "end": 965440,
    "text": "Okay, thank you, Mayor Reed. Following up on the Mayor's comments, I have a certified monarch waystation in our yard, which some of you may have heard of. It's through Monarch Watch at the University of Kansas. So besides, in public parks and public spaces, individual homeowners really can make a difference for the monarch butterfly. Really, even one milkweed plant in your yard can make a huge difference because as the mayor said, that is the only food that the monarch caterpillar will eat. And so if you have a milkweed plant in your yard and the caterpillars can start their life cycle and of course, metamorphosis into the butterfly, the other thing you can do as a homeowner is have nectar plants in your yard, particularly late blooming nectar plants in the fall. The migration to Mexico in this area is August through October. And so if you have a nectar source in your yard that the butterflies can access during that southward migration, that is very helpful to them. So some ideas for planting in your yard would be goldenrod or aster so that they've got that nectar source on their way to Mexico. The good news is that in this past overwintering season in Mexico, There was a 64% increase in the amount of butterfly and the amount of monarchs that were there. So we're showing some improvement. We're not really there yet to the goal, but we're moving in the right direction. So that was good news from the overwintering sites in Mexico. So you can, if anyone wants to visit my yard this summer, you can reach out to the city clerk and get my address. But you can actually have butterflies flying around you. You can see caterpillars in the yard, and it's very exciting. Mary, my colleague from the women's club also has a lot of milkweed in her yard. Cindy Meyer has milkweed in her yard. And there are probably a number of you who also have that. It's very exciting. It's a science project going on right in your yard. I've had field trips from our daycare down the street. I've done some stuff virtually for the science teacher at Daniel's Run. So it's very exciting. So I'm happy to guide anybody who wants to do this project? So turn it over to Stephanie Johnson has got."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 965760,
    "end": 1179580,
    "text": "Thank you, Jen. You covered all of it. Well. So the commitment to, you know. And I've got astros in my yard. And. And these plants are beautiful, too. So think about the fact that when you choose what you plant in your yard, there's all kinds of benefits. Like you get to have butterflies. Okay with that? A. So I'm going to now invite the Women's Club of Fairfax to join me up here so that we can talk about the 70th anniversary of this very august body of women who exist here in our city. Everybody, this is wonderful. Everybody in. Everybody in. Everybody in. Lovely to see everyone. Lovely to see everyone. Is everybody in? Okay. We all here? Okay. Whereas the Women's Club of Fairfax was established in 1956 by friends wanting to make a difference in the community and further their commitment by registering their club with the state and national general federation of women's Clubs. And whereas as the town of Fairfax became the city of Fairfax, the area grew from a quiet rural community into a bustling region. The women's club was an active participant in keeping the history and small town feel alive through generous contributions of time and financial support of many worthy causes. And whereas. The Women's Club of Fairfax continues to contribute funds and volunteer services to Fairfax cultural and civic organizations and events such as the Independence Day celebration, City of Fairfax Band Association, Fairfax Volunteer fire Department, the inter service club council and the chocolate lovers Festival and has adopted the school street park, providing quarterly maintenance of weeding and planting as well as donating a park bench to encourage use of the park. And whereas. The Women's Club of Fairfax supported the construction of the Turning point Suffragist Memorial in Occoquan Regional park and annually offers an achievement scholarship to a graduating local high school senior who will attend a Virginia university or college. And whereas. The Women's Club of Fairfax offers programs focusing on issues of importance to women, family, families and the community and continues today as a unified and diverse group of women dedicated to enhancing the lives of families and strengthening their community through volunteers. Volunteer service. Now, therefore, I, Catherine S. Reed, mayor of the city of Fairfax, Virginia, in concert with the city council, do hereby commend the Women's Club of Fairfax on their 70th anniversary and encourage all citizens of the city of Fairfax to recognize, commemorate and celebrate the wonderful contributions the Women's Club of Fairfax has made to the betterment of the city of Fairfax. And with that. Who is speaking? Martha, come on. The president of the Women's club."
  },
  {
    "speaker": "Martha",
    "speaker_source": "correction",
    "speaker_source_detail": "Corrected from Mayor Catherine Read",
    "start": 1182000,
    "end": 1208820,
    "text": "Good evening. I just want to say that we feel very fortunate to be a part of the city, and we enjoy doing as much as we can to be supportive of the city. And I think it's pretty impressive that we have sustained ourselves for 70 years, considering all the different ups and downs of the past 70 years. And we look forward to serving you for many more years. And thank you."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "Corrected ASR error: Aliyah -> Elijah Tibbs",
    "start": 1267780,
    "end": 1439720,
    "text": "All right. I'll now ask our Fairfax City police dispatchers to come down here so we can celebrate you. Come on. It's cool to stand up here and just be stared at. Trust me, not awkward at all. All good. All good. You guys are important. So important. Very important. All right, everybody in. The cutest. All right. Whereas the week of April 12th through 18th, 2026, has been designated as National Public Safety Telecommunicators Week, a time to raise awareness and recognize the critical contributions of highly trained telecommunications professionals who provide vital 911 emergency assist to those in need. And whereas emergencies requiring police, fire or emergency medical services can occur at any time and the prompt response of police officers, firefighters and paramedics is essential to the protection of life and preservation of property. And whereas the safety of police officers, firefighters and paramedics depends upon the quality and accuracy of information obtained from citizens who contact the city of Fairfax emergency communications center. And whereas public safety telecommunicators are the first and most critical point of contact our residents have with emergency services, serving as the vital link between the public and emergency responders. And whereas public safety telecommunicators contribute substantially to the apprehension of criminals, the suppression of fires and the treatment of patients, demonstrating professionalism, understanding and dedication in every call they handle. And whereas within the police department, a dispatcher of the year is nominated by police personnel to recognize an individual for exceptional performance exemplifying the commitment and excellence demonstrated by all emergency dispatch professionals in our city each and every day, 24 hours a day and seven days a week. Now, therefore, I, Catherine S. Reed, mayor of the city of Fairfax, do hereby proclaim April 12 to 18, 2026, is National Public Safety Telecommunicators Week in the city of Fairfax and encourage all members of our community to join in extending our warmest measure of gratitude and support to our public safety telecommunications dispatchers, including our award recipient, Elijah Tibbs, the 2025 Dispatcher of the year, who provides critical and essential services daily to the countless number of residents, business owners and visitors within our community. So with that, Elijah."
  },
  {
    "speaker": "Group",
    "speaker_source": "correction",
    "speaker_source_detail": "Brief unidentifiable utterance - labeled REDACTED in error",
    "start": 1440760,
    "end": 1441120,
    "text": "No."
  },
  {
    "speaker": "Group",
    "speaker_source": "correction",
    "speaker_source_detail": "Brief unidentifiable utterance - labeled REDACTED in error",
    "start": 1441120,
    "end": 1441640,
    "text": "Cease."
  },
  {
    "speaker": "Group",
    "speaker_source": "correction",
    "speaker_source_detail": "Brief unidentifiable utterance - labeled REDACTED in error",
    "start": 1445160,
    "end": 1445560,
    "text": "Chief."
  },
  {
    "speaker": "Councilmember Stacy R. Hall",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1451640,
    "end": 1551540,
    "text": "Good evening, everybody. You know, it's A great opportunity to be here with you and celebrating. So such an important, important group of professionals in our public safety world. I just want to introduce everybody really quickly. Our dispatcher, Ms. Araceli Gonzalez. Ms. Courtney Ellis. Elijah Tibbs, who was just introduced as our dispatcher of the year for 2025. Our communications and records supervisor, Ms. Cynthia Tetterton. Our lieutenant, Ms. Stephanie Sharp, who oversees the entire operation, and then Captain Brock Rutter, who oversees the administrative services division. With them. There's another six dispatchers that help answer all the phone calls from people within our city. Whether you're living here, working here, visiting, if you have any type of emergency, if you need directions somewhere, you call the police and they answer. And it's something beautiful to watch. If you ever have the opportunity to be in a911 center and to see what happens, particularly when there's a critical situation occurring in the city and all of them come together and whether it's. You have to understand what they do. They take the phone call, they're a detective, they're asking questions. They're figuring out what it is that's happening, where it's happening, what's that vital information that has to get routed to our responding police or fire personnel at the same time. They're typing it all and routing it to the police officers and emergency personnel, real time as they're typing it fast, figuring out what to ask, what's the next question, typing it in and routing it to the right people and assigning the right personnel to respond to that call. It's incredible. And so I really thank all of our dispatchers, appreciate everybody supporting them and for our proclamation. Mayor, thank you so much."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "correction",
    "speaker_source_detail": "Corrected from Councilmember Tom Peterson",
    "start": 1556580,
    "end": 1562110,
    "text": "And who is. Who is this officer? Officer I forgot to introduce?"
  },
  {
    "speaker": "Unknown Speaker",
    "speaker_source": "correction",
    "speaker_source_detail": "Corrected from Stacy Hall",
    "start": 1562110,
    "end": 1562670,
    "text": "Sherry."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "correction",
    "speaker_source_detail": "Corrected from Councilmember Tom Peterson",
    "start": 1563230,
    "end": 1566190,
    "text": "Officer Sherry. Okay, Officer Sherry."
  },
  {
    "speaker": "Group",
    "speaker_source": "correction",
    "speaker_source_detail": "Brief unidentifiable utterance - labeled REDACTED in error",
    "start": 1568270,
    "end": 1568910,
    "text": "Okay."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "correction",
    "speaker_source_detail": "Corrected from Councilmember Tom Peterson",
    "start": 1569390,
    "end": 1570390,
    "text": "Wonderful, wonderful."
  },
  {
    "speaker": "Councilmember Stacy R. Hall",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1570390,
    "end": 1573790,
    "text": "Sher's our wellness dog, so she. She's here to support everybody."
  },
  {
    "speaker": "Group",
    "speaker_source": "correction",
    "speaker_source_detail": "Brief unidentifiable utterance - labeled REDACTED in error",
    "start": 1573950,
    "end": 1576510,
    "text": "So we are going to nab a picture. All."
  },
  {
    "speaker": "Group",
    "speaker_source": "correction",
    "speaker_source_detail": "Brief unidentifiable utterance - labeled REDACTED in error",
    "start": 1586680,
    "end": 1586920,
    "text": "Work."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "correction",
    "speaker_source_detail": "Corrected from Councilmember Billy Bates",
    "start": 1639300,
    "end": 1641620,
    "text": "We can move on to the adoption of the agenda."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "correction",
    "speaker_source_detail": "Corrected from Councilmember Tom Peterson",
    "start": 1643700,
    "end": 1649400,
    "text": "Is there a motion to approve the agenda? I move to adopt the agenda as presented. Is there a second?"
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "correction",
    "speaker_source_detail": "Corrected from Councilmember Stacy Hall",
    "start": 1650120,
    "end": 1650520,
    "text": "Second."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "correction",
    "speaker_source_detail": "Corrected from Councilmember Tom Peterson",
    "start": 1651480,
    "end": 1654040,
    "text": "The motion has been made and seconded. A roll call vote."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1654760,
    "end": 1655880,
    "text": "Council Member Amos."
  },
  {
    "speaker": "Councilmember Stacy R. Hall",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1655880,
    "end": 1656280,
    "text": "Aye."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1656360,
    "end": 1657360,
    "text": "Councilmember Hall."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1657360,
    "end": 1657800,
    "text": "Aye."
  },
  {
    "speaker": "Councilmember Billy M. Bates",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1657800,
    "end": 1659120,
    "text": "Council Member Hardy Chandler."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1659120,
    "end": 1659520,
    "text": "Aye."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1659520,
    "end": 1660680,
    "text": "Council Member Peterson."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1660680,
    "end": 1661080,
    "text": "Aye."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1661160,
    "end": 1662200,
    "text": "Councilmember bates."
  },
  {
    "speaker": "Councilmember Stacy R. Hall",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1662200,
    "end": 1662640,
    "text": "Aye."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1662640,
    "end": 1663880,
    "text": "Councilman McQuillan."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1665000,
    "end": 1665480,
    "text": "Aye."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1666360,
    "end": 1667800,
    "text": "Motion passed unanimously."
  },
  {
    "speaker": "Councilmember Rachel M. McQuillen",
    "speaker_source": "correction",
    "speaker_source_detail": "Corrected from Councilmember Tom Peterson",
    "start": 1667960,
    "end": 1668520,
    "text": "Sorry."
  },
  {
    "speaker": "Councilmember Billy M. Bates",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1669080,
    "end": 1678010,
    "text": "All right, we will go on to initial general public comment. I had taken 10 speakers sign up by 5pm today, so I will call the first one up, which will be Anita Light."
  },
  {
    "speaker": "Anita Light",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1686890,
    "end": 1770010,
    "text": "Good evening, Mayor Reed and members of city council. My name is Anita Light and I'm here tonight in three capacities. First is the chair of the Fairfax Village in the City Advisory Board, a resident of Fairfax City, obviously, and as an older adult. As chair of the Fairfax Village and the City Advisory Board, we wanted to emphasize our support for the Willard Sherwood center, as noted in our letter to you all, dated April 6th. In that letter, we noted that supporting the new Willard Sherwood center would help make accessibility for older adults easier and safer. We also noted that this project was a community partnership effort with the county as well as the residents of both the city and the county. And finally, we highlighted that this project is a long term investment for the future of the city. And as an additional note on the advisory board, and for a more important reason, we really support advancing the Willard Sherwood center to help enhance the Villages Expo that we had this past Friday, which was a huge success. And if we had even, even better facility with better parking, it would help that event even better. And as a city resident of the city, I support the Willard Sherwood center because this facility will afford."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1770720,
    "end": 1866460,
    "text": "A generational opportunity for programming for older adults and children and support the healthcare needs of our city. The partnership with the county has been long standing and as a result, the city is able to do more for the residents than they would otherwise be able to do. For instance, on social services, emergency dispatch, libraries, court services, and schools, to name a few. Without these partnerships, the cost to our residents would be significantly more if we had to provide these basic services on our own. I've been a lifelong proponent of continuous improvement in organizations, and while the Willard Sherwood center is not an organization, it is a joint partnership with the county that needs to be continuously improved and nurtured to avoid even further costs. As an older adult, which I'm getting older and older by the minute, I support the Willard Sherwood center project because participating in programs at Green Acres is potentially hazardous to my physical well being. When I attended events at the Green Acres Center, I had had recent knee surgery and since parking at the Green Acres center is at a premium, walking to the entrance was very difficult and walking down those steps to get to the front door was even more difficult. And then once you get inside the building, you have more steps to get to some of the rooms and that gets increasingly difficult for the older people. Get having access to new modernized Willard Sterwood Center."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1867180,
    "end": 1867660,
    "text": "Oh."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1868700,
    "end": 1886630,
    "text": "So while I urge you to while there is a cost to modernization and there will be additional cost to the center, I urge you to support its development that will help the more than 9,000 older adults in Fairfax City. And and we appreciate and thank you for your consideration. Thank you."
  },
  {
    "speaker": "Kevin Anderson",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 1888150,
    "end": 2103630,
    "text": "Our next speaker is Kevin Anderson. I want to thank you for this opportunity. I am a county resident and a member of the Young at Heart Senior Center Council and I'm here to speak in favor of the Willard Sherwood Project. Green Acres is an apt name when you consider the ball fields and the surrounding grounds, but the building, the H VAC system and the utilities can hardly be considered green. Since I don't have access to the specifics of Green Acres, I utilized AI to assist me with my research and I could have used the AI to write my comments for me, but I was thinking that might be a little bit cheating. Plus, I didn't want to sprout a six finger on my hand either. So my research found that a 41,000 square foot school built in 1961 currently has an average cost for utilities ranging from 30,000 to $54,000. Considering the GA I'm sorry, has the original 163 steel frame windows and six exterior doors with windows all single pane. I'm pretty comfortable with the idea that the expense is on the higher end of that range. Compared to the energy efficient and sustainable features planned for the project. The anticipated savings would be in the 30 to 50% annually and could be even as high as 70%. This of course will have to be observed with the actual charge that we incur to see what percentage is actually saved. But I'm willing to bet that it will be on the higher end. Beyond the potential cost savings, there are numerous environmental benefits to the project design. It will have a positive impact on the planet that we hand off to our children or if you're like me, to your grandchildren. Some of these elements are the fact that the project is LED gold certified and it has features like rooftop solar panels, indoor water reductions features, LED lighting, light pollution remediation and high performance building elements to retain heating and cooling and many others. Another subject I'd like to talk about is routines. We all have them. They usually evolve over life events. But if this project fails to move forward and Grain Acres has to close down for major renovations or rebuild, it's going to be an abrupt change to many of our members routines. And basically what I'm saying is that if we build a new center and we do a gradual transition to the new one, it'll be more of an evolutionary change to the routine. So I beseech you to approve this project and I thank you for your time. Thank you. Our next speaker is Douglas Stewart."
  },
  {
    "speaker": "Douglas Stewart",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 2114750,
    "end": 2257700,
    "text": "Good Evening, Douglas Stuart. 10822 Maple Street. I'm here to also voice my support for moving forward with the Willard Sherwood Center. I appreciate the discussions you've had about this project. My wife and I have lived here for 22 years and I realize this project has both operating and capital costs that we have to reckon with and that we'll see in our tax bills. The costs are significant, but I believe the benefits will far outweigh them. And really we're talking about a multi generational community center, something for all ages with first class preventive health services. We're talking about a new third place for our youth and people of all ages. We're talking about outstanding facilities that the whole community can congregate in and enjoy. People from 8 to 80 to 90 or even 6 to 90 or what? I mean there's something in this for everyone. And also just the preventive health, including serving our residents in Fairfax City will be outstanding, including dentistry. It's going to improve quality of life for so many people in so many different ways. The costs are significant. We know we're going to see higher tax bills. We know that. And sometimes when you're looking at the future, what are we going to have in the future here? It's uncertain. It's an investment. But it's going to be here for generations. And I'm confident that in 30 years, our kids today, or the grandkids, the kids of our kids are going to be talking about this and have memories. I did this. Do you remember when we did this at the community center? It's going to be part of our community and it couldn't be in a better place right near our Signature park and our downtown. So I think it's a fantastic investment. The previous speaker mentioned the LEED gold and I just would just emphasize that. I hope you stick to that LEED gold standard. That's a really high standard for energy and water efficiency. And if we hold to that, as the previous speaker mentioned, we're going to significantly save in energy costs and other costs from like stormwater management. So I think this is going to change people's experiences of the city for generation and I strongly support it. Thank you."
  },
  {
    "speaker": "Janet Jaworski",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 2260100,
    "end": 2360010,
    "text": "Our next speaker is Jan Jaworski. Good evening Mayor Reed and members of the City Council. I also am here to Janet Jaworski, 3621 Heritage Lane. For the record, I also am here to lend my support to the Willard Sherwood Project. I do wear a number of hats in the city, as you know, so these are my comments as a resident and not representing any organization or department for which I volunteer. Pete and I have lived here for 26 years and honestly, I think the need for a community center has been part of the dialogue for the entire time that we've lived here. In fact, during my six year tenure on the Planning Commission from 2014 to 2020, including a three year stint on Prab, this was a huge topic of conversation. And this is going back more than 10 years from now, the need for a full service community center. So I do support it for all the reasons that you've been hearing from from all of the other residents coming up to support it. I'm going to focus on something a little bit different. Although I am a member of the senior center, but I'm going to try to highlight some benefits for adults of all ages. As a former competitive athlete, I think the walking track, the gym, the fitness center are going to be so key to both the physical and mental health of our residents. As we all know, mental health and physical health are intertwined and a happy, healthy, both mentally and physically. Population here."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 2360560,
    "end": 2446790,
    "text": "Is really something that you cannot put a price tag on. I realize, as Mr. Stewart said, we all know there's a price tag involved. We're mindful of that. But to me, the advantages far outweigh the disadvantages. I love the fact that it will be multi generational. You know, our city motto is live life connected. I think this is a great way that we can all connect and share experiences together. There will be a number of meeting rooms there, as you know, so it will be a place to gather, exercise and really build community. Secondly, it's going to be walkable for a lot of us. I know that's not true for all neighborhoods, but for my neighborhood in Daniels Run woods, it will be walkable. And we can get a jump start on our workout routine by walking to and from, which I think will be great. It also is accessible for public transportation, which is wonderful. Lastly, our relationship with the county. I was so pleased to hear that you had a successful meeting with the county last week. That's fantastic. I appreciate the fact that there were no objections to the timeline and that's really great news. I think continuing to nurture that relationship with the county is huge and this is a great way that we can partner with the county moving forward. So I would ask for your yes vote on April 28th to move this forward. And I appreciate your time."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 2447620,
    "end": 2448100,
    "text": "Thank you."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 2450100,
    "end": 2452020,
    "text": "Our next speaker is Janice Miller."
  },
  {
    "speaker": "Janice Miller",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 2461540,
    "end": 2646840,
    "text": "I'm a little shorter than Janet. Good evening, ladies and gentlemen, Mayor Reed, members of council staff, residents and guests. My name is Janice Miller and I am here to support moving forward with the Willard Sherwood project. And I support council members authorizing the the EDA to sell revenue bonds to finance this project. Questions have been raised recently regarding the economic advantages of this proposed project. Please consider the following. Willard Sherwood would be a long term economic anchor. It would strengthen downtown vitality due to its central location. It would generate consistent weekday activity that will support downtown retail and services. It would increase pedestrian activity in the downtown area. It would reinforce Old Town as a hub for daily life and not solely as a spot for dining out, nightlife and or special events. Willard Sherwood would demonstrate capital leverage and fiscal efficiency. The capital costs are divided between the county and the city based on programmatic usage. The city avoids land acquisition costs, demolition costs and site preparation costs. The shared infrastructure and parking reduce capital duplication. Energy efficient design lowers operating costs. Willard Sherwood will support workforce and talent competitiveness. It will help attract and retain public and private sector employees and professional households. It will reinforce the city's identity as a service rich community. It will enhance the city's appeal relative to competing jurisdictions. Unlike market driven projects, the center provides enduring economic value across all business cycles. All these factors support office occupancy, mixed use development and economic security. Willard Sherwood advances the city's strategic priorities and economic development goals. It maximizes limited land resources and preserve green space through joint development. It uses external funding to reduce city exposure. It strengthens downtown vitality. It supports quality of life. It builds on past city county partnerships and establishes a model for future city county collaboration. In summary, by providing the opportunity for enhanced business tax income, this project will deliver sustained economic value that will ultimately far exceed its direct fiscal cost. There are many in the audience who support Willard Sherwood. Would those who support this project are willing to pay reasonable fees for usage and approve of their tax dollars paying both capital cost and operating costs? Please stand up."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 2648840,
    "end": 2650680,
    "text": "Our next speaker is Dale Lacina."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 2651480,
    "end": 2651960,
    "text": "Thank."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 2664700,
    "end": 2824020,
    "text": "You. Good evening, Madam Mayor, city council members and assembled city staff. I have. I'd like to speak to just two issues in my allotted time. The first is the Willard Community Center. All the good things that have been said about it I support. I would add one other thing that I didn't hear yet and that is combining the community center in the center of the city. I think it just makes sense to me and it's a great opportunity to reinforce Old Town as a hub of daily activities which has been necessary for a long time. And we've talked about that quite a bit. So I recommend that you support that issue. The other one has to do with the Fairfax Renaissance Housing Corporation, which is an organization that provides city of Fairfax homeowners an attractive opportunity to upgrade and improve the quality of the city's residential neighborhoods. Over the past 23 years of its existence, it has provided funding to 290 improvement loans and has not lost a single penny to a bad loan. Plus, the city gets back money from the housing Corporation program due to the permanent improvements that are made. And thus the tax that goes with that permanent improvement goes with the home, okay? And so when the increase comes for that, the city receives a return on its investment and it continues and continues. So this program was not funded last year and now we can't do any loans at all because they don't have funds for it. And so I strongly urge that this City Council fund it for next year so that we can continue this program because it returns money to you and the persons that the people that get the improvements like it a lot, believe me. I thank you for your kind attention."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 2826340,
    "end": 2828340,
    "text": "Our next speaker is Rebecca Rader."
  },
  {
    "speaker": "Becky Rager",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 2839630,
    "end": 2950010,
    "text": "Good evening. Thank you for the opportunity to speak with you tonight. My name is Becky Rager. I live at 4141 Evergreen Drive. Been there for 31 years. I'm a current member of the Fairfax Village in the City Advisory Board. I spoke to you last month in overall support of the Willard Sherwood Health center and the community center. I'm here today to briefly express how the village and the city could enhance services as a result of the new facility. I'm mentioning a few possibilities today as we move forward. The advisory board members, village members and volunteers can brainstorm other possibilities for expanded services that directly support older adults and those with disabilities beyond what is currently available. We will also work with the Willard Health center and the Green Acres staff to create new programs which could include, and I'm just listing a few intergenerational activities such as tutoring or reading to the children in the child care center Working on shared craft projects in dedicated spaces where projects could remain until completed growing and maintaining a rooftop herb garden and creating a gardening circle working with the neighboring Willard Health center to have a memory cafe once a month where people who are in the early stages of cognitive impairment and their caregivers can meet, socialize and trade ideas developing workshops designed to improve memory and cognitive function creating a digital storytelling club where seniors use technology and record their life stories and conducting a vintage hat."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 2950240,
    "end": 3001930,
    "text": "And fashion showcase where members bring in their vintage collections and show them and then discuss the stories behind them. All of these proposed suggestions could be done without additional staffing costs as members are not just consumers, they are staff. Our village consists of members and volunteers with an extensive variety of backgrounds and experience. For example, a member might receive a ride to the doctor one day and facilitate a workshop the next. This creates a sustainable model for future programs without additional cost. I believe the new Willard Sherwood facility, with all the infrastructure enhancements will provide is necessary to continue to deliver modern, equitable services for the entire community."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 3002770,
    "end": 3003250,
    "text": "Thank you."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 3005330,
    "end": 3007170,
    "text": "Our next speaker is Alan Glenn."
  },
  {
    "speaker": "Councilmember Stacy R. Hall",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 3016450,
    "end": 3192620,
    "text": "Thank you. Alan Glenn, longtime resident of the city and now a resident just outside the city. I wanted to speak tonight also in favor of the project that Willard Health Center, Sherwood center, both on my wife's behalf, Judy Blanchard and myself were strongly in support of it. We've benefited from some of the services over the years. Our kids were vaccinated at the health center in their early childhood period. We've had other counseling and services over the years. Both of us have used the senior center and continue to be members there. I think the expanded opportunities for child care and public health that will be offered and available through this project are very much in demand to me. This project is one of a number that I consider crown jewels in the community where the city partners with the county and coming up with a wonderful facility to serve everyone, including the public schools where both our kids went and the public library that we've used and the. And the health centers. Personally, I think you all have a difficult job as elected leaders with to a two year term where you have to consider the strategic needs of the community and balance them against costs and budgetary issues. But I think in this case the project will solve a need to re update and replace the senior center that's now at Green Acres and provide better health and public services and childcare and health, early childhood health for residents. The nice thing about this is it serves everybody in the community regardless of age, income strata or which neighborhood you live in. So to me it's definitely needed and I strongly support it. Thank you very much. Oh, as long as I've got 30 seconds left. Let me just say Mr. Lastina, who is the president, previous speaker, I would like to endorse his comments. I served on the board with him for five years of the Housing Renaissance Corporation. That was one of three city boards that I've had the privilege to serve on over the years. And I think that board and the funding from the City served an important need to maintain and upgrade existing housing stock in the city. Thank you."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 3194650,
    "end": 3196570,
    "text": "Our next speaker is William Pitchford."
  },
  {
    "speaker": "William Pitchford",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 3206170,
    "end": 3422460,
    "text": "Good evening and thank you for the opportunity to speak this evening. My name is William Pitchford. I live on School street in the city of Fairfax. In two weeks, at the April 28th city council meeting, you're you will be asked to approve a resolution to proceed with the Willow Sherwood Health and Community center project and a resolution for the Economic Development Authority to issue bonds to finance such capital projects. I'm asking you to approve both resolutions as it is the best option for the citizens of Fairfax City and the city's overall economic and infrastructure development. I'd like to offer a few points on why you should approve these two measures. As you have heard throughout this evening, the citizens of Fairfax City are in desperate need for a community center that meets their needs and have expressed this with broad support for the project through two years of design reviews with broad support for the two years design reviews and approvals from previous current City Council. This is probably the most vetted capital improvement project the city has undertaken. The new Willard Sherwood Community center will be a joint venture project with Fairfax County. The cost of building and operating the facility is shared, significantly reducing the burden to the city taxpayers. This is a generational opportunity for the citizens of Fairfax. Another opportunity like this will most likely not come around again in our lifetime. The current Green Acres facility is completely inadequate to meet the community's current and future needs. The facility was built in 1961 as an elementary school. That was before schools had air conditioning. It was retired in 2000. It was never intended to be a community or senior center. The building is well beyond its youthful lifespan. It's located in the center of a residential community, has no public transportation access, poor ADA compliance and a dangerous parking lot, especially at night. I had the honor of attending a Fairfax City Citizens for Smarter Growth meeting at Green Acres in February of this year. Like most community service organizations, this is where they have meetings. And just like this council meeting, it started at 7pm Unlike the normal council meetings, it ended at the decent hour of 8:30, which was still well past sunset when leaving. When leaving the meeting, I was absolutely shocked to walk out to a darkened parking lot, having to reverse a narrow steep staircase to find my car. I tried to imagine what someone 10 to 15 years older than I would do. Basically, they would stop participating in their community after dark. For those of you who have any reservations about the Neeford project, I would challenge you to hold an official city meeting at Green Acres. It doesn't have to be the current. It doesn't have to be the next council meeting, but it could be a planning commission or economic development authority meeting. In conclusion, I'm ask you to approve the two resolutions at the April 28 council meeting. Thank you. Our last speaker is Toby Sorenson."
  },
  {
    "speaker": "Toby Sorenson",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 3434630,
    "end": 3540010,
    "text": "Good evening. Toby Sorenson, 10137 Spring Lake Terrace Mayor Reed and council members. The reason I am once again here to speak about supporting the Willard Sherwood Health and Community center is because many of us still do not know whether you are going to vote to fund it on April 28th or not. If any of you are still undecided to vote, please consider the following. If you vote for the funding, there are many things we do know. We know what the city's share of the joint project will be thanks to the guaranteed maximum pricing contract. We know what the operating costs will be thanks to the research done by the project consultants. We know the basic level of class and rental fees that will cover operating expenses. We know the higher level of class and rental fees that will cover operating expenses plus provide a surplus that can be put toward the yearly bond payment. We know what the bond payment will be if the city goes to bond this spring. We know that we will be able to keep a senior center and have it located in a modern facility with better services. We know that we will be able to keep a much needed preschool in the city. We know that we will have a well located community center that will draw people and businesses to the downtown area. We know that we will have continued access to important health department services right in the middle of the city. Finally, we know when this project will be completed. If you do not vote to fund Willard Sherwood, there are many things we will not know. Would we begin again to create a plan to build or rebuild a community center? How much would that new planning cost? Would a new."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 3540400,
    "end": 3622620,
    "text": "Project be located at Green Acres? Would a new project be located elsewhere? Where would that be and how much would it cost? How far into the future will we be looking and how much will the cost of bonds be at that time? If we do nothing, will we lose the senior center and the preschool? Since the City Council and the County Board of Supervisors signed a letter of understanding which for full design and construction of the joint project, would the county expect the city to compensate them for the money they have spent on the project so far? Would the county expect the city to compensate them for the money it will need to begin their planning and design process anew? Would the county choose a different location for the health center, one that would not be in the city if the county chose a different location? Or what would they decide to do with the land that they own next to the Sherwood Center? We want to continue to have a senior center and a preschool and community spaces for our residents as well as to have a health department located within the city. If you believe you have a hard decision to make about funding Willard Sherwood, think also about the really hard decisions you will have to make if you don't fund vote to fund it. Thank you for listening."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "unknown",
    "speaker_source_detail": "",
    "start": 3625820,
    "end": 3701630,
    "text": "We can Move to the Consent Agenda okay, before we move forward, I want to make a take a moment to briefly address consent agenda items 6F through 6K and 6M. These items are administrative in nature and represent the first step in a multi step process, what we refer to as the introduction phase. This step is intended to formally notify our residents and business community of the city's proposed actions. There will be a full opportunity for public input at the next stage, which is the public hearing scheduled for our next regular meeting on April 28. Following that, the third and final step will be council consideration and action as part of Budget adoption night on May 5th. So again, tonight's action is simply to move these items forward in the process and ensure the community is informed and has the opportunity to participate. Are there any questions on any of the items on the Consent Agenda from the dais? Seeing none. Is there a motion?"
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3702750,
    "end": 3709790,
    "text": "I move to approve the consent agenda items 6A through M as presented and the accompanying motions in the staff reports."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3710830,
    "end": 3721150,
    "text": "Is there a second? Second we have a motion made by Council Member Stacy Hardy Chandler and seconded by Council member Peterson. A roll call vote. Council member McQuillan?"
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3722270,
    "end": 3722750,
    "text": "Aye."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3722830,
    "end": 3728100,
    "text": "Council member Bates? Aye. Council Member Peterson Aye. Council Member Hardy Chandler?"
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "correction",
    "speaker_source_detail": "Roll call vote response - clerk read back",
    "start": 3728100,
    "end": 3728580,
    "text": "Aye."
  },
  {
    "speaker": "Councilmember Stacy R. Hall",
    "speaker_source": "correction",
    "speaker_source_detail": "Roll call vote - Hall responded Aye",
    "start": 3728660,
    "end": 3728760,
    "text": "Hall Aye."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "correction",
    "speaker_source_detail": "Roll call vote - Amos responded Aye",
    "start": 3728760,
    "end": 3728860,
    "text": "Council Member Amos Aye."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "correction",
    "speaker_source_detail": "Motion result kept, vote responses moved to separate turns",
    "start": 3728660,
    "end": 3742820,
    "text": "Motion passed unanimously. Will go to appointments to boards, commissions, and advisory committees."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3742820,
    "end": 3804930,
    "text": "I move to appoint the following applicants. Commission on the Arts. Appoint Melissa Miller for a remainder of a three year term extending through July 9, 2027. Appoint Kenneth Kraftchyk for a remainder of a three year term extending through October 26, 2028. Appoint Ann Morrison for a three year term extending through April 14, 2029. Reappoint Sharon Clark Chang for a three year term extending through February 11, 2029. Continuum of Care. Appoint James Gillespie for a two year term extending through April 14,2028. Environmental Sustainability Committee. Appoint Lauren Oliver for a remainder of a three year term extending through February 11, 2028. Appoint David Fleischer for a three year term extending through April 14, 2029. And exclude Nova Parks appointments until May 12."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3805010,
    "end": 3813870,
    "text": "Is there a second? Second. There has been a motion and a second. Is there discussion on this motion?"
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3814190,
    "end": 3819870,
    "text": "Yes. Councilmember Peterson, may I ask why the final two appointments are being pulled?"
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ video verification 2026-04-29",
    "start": 3820750,
    "end": 3822270,
    "text": "Council Member Hardy Chandler."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ video verification 2026-04-29",
    "start": 3822910,
    "end": 3833310,
    "text": "There has been additional clarity on procedure that allows for input while safeguarding conflict of interest, and I want additional time for that to happen."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ video verification 2026-04-29",
    "start": 3833870,
    "end": 3836270,
    "text": "Can you clarify that? I'm not following that."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ video verification 2026-04-29",
    "start": 3837790,
    "end": 3845710,
    "text": "Each candidate can be considered individually, and while I would recuse myself from one of the candidates, I do want to have input on other candidates."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3846190,
    "end": 3853950,
    "text": "Are you saying that you are going to vote on slots in which your husband is an applicant?"
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3854990,
    "end": 3863650,
    "text": "I'm going. Individual people are on their own merit, and I would like to have input on the individuals who are candidates on their own merit."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3863730,
    "end": 3867490,
    "text": "So we have three applicants for two slots, one of whom is your husband."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3868290,
    "end": 3868690,
    "text": "Right."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3868850,
    "end": 3876450,
    "text": "Okay. Under state law, for jurisdictions that follow it, that's normally considered a conflict of interest."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3876690,
    "end": 3881890,
    "text": "I would recuse myself, as I have historically, on the vote for my husband for the slot."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3882050,
    "end": 3886690,
    "text": "Will you recuse yourself from a slot in which your husband is one of the applicants?"
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3891740,
    "end": 3900060,
    "text": "It is my understanding that there is appropriate input that can be made on other candidates for this position, and I would like to have that input."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3900460,
    "end": 3919850,
    "text": "Okay, so the simple question here is whether you are going to be voting on a slot. There are two slots with three applicants where your husband is an applicant. Because normally, under state law, for jurisdictions that follow it, this is regarded as a clear conflict of interest."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ video verification 2026-04-29",
    "start": 3920650,
    "end": 3925290,
    "text": "Each slot is independent. Okay. And they're not the same. Slide. Okay."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ video verification 2026-04-29",
    "start": 3925290,
    "end": 3929610,
    "text": "I think that's. Let me recognize council member McQuillan."
  },
  {
    "speaker": "Councilmember Rachel M. McQuillen",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ video verification 2026-04-29",
    "start": 3934170,
    "end": 3953060,
    "text": "Our residents applied for these roles in good faith. They interviewed in good faith. Council discusses these applications through the established process. We should respect the process. Vote and move forward. That's how I feel."
  },
  {
    "speaker": "Councilmember Stacy R. Hall",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ video verification 2026-04-29",
    "start": 3954020,
    "end": 3957380,
    "text": "Thank you, Council Member Hall."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 3959060,
    "end": 4043020,
    "text": "I also think that we have taken a very, very long time, especially on this one item. There are two people that are currently serving in this role who are now one year beyond their designated term. And I do not and have not thought that it was appropriate that they continue to serve simply because this council can't come to an agreement. And I think we had what I thought was a very productive meeting a few weeks ago where we came out with two, two names that you can see on the motion. And I understand that maybe you have a different thought now that you understand maybe you can vote on a different spot or different thing. But I still think that this is very messy. And I think that we are in a situation where we are at a split vote. And unfortunately, math often is used against certain members of council when it comes to making decisions on other things. There have been many high density housing options that have passed simply because there is a vote and it is split and the mayor can break a tie. And I do not agree with that in its own merit and I simply do not agree with it now."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4044090,
    "end": 4072300,
    "text": "Thank you. And I would point out that the first 63 years of this city's history, the mayor was not excluded from the discussions or appointments to boards and commission until this council. And so whether I have feelings about that or not, this council decided that, which is why we have an even number of people voting on these appointments. Up until this council. As far as the mayors that I have spoken with previously, this was not an issue. So there are issues here for sure. There are on many fronts."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4072380,
    "end": 4129850,
    "text": "Councilmember Amos So when the initial discussion happened in March, I was clearly not here for that. Towards the end, since I was out of the country, I got back in my understanding. Was there supposed to be a recusal? And I really think for me, there's only one question that really needs to be answered and that would probably come from our city attorney, is that, per your review, should Councilmember Hardy Chandler have been included in the vote for two of the appointees, excluding her husband? So one of the nice things about the State and Local Government Conflict of Interest act is that decision is left to the individual member. I have my opinions as to whether it's appropriate for a member to vote for a position in which his or her husband."
  },
  {
    "speaker": "City Attorney",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4130640,
    "end": 4144720,
    "text": "Family member is a candidate. I will say I think the answer to that question is not really a legal one. So council member Hardy Chandler is taking her own counsel on this, and that is all I will say on that."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4145120,
    "end": 4166410,
    "text": "Thank you. So to follow up on that, I completely understand that this is a frustrating circumstance and has been for some time. Ultimately, due to policy and procedure in the existing rules, it would be on Stacy Hardy Chandler, which means, I believe, that it would be necessary to push it to May 12th and have additional discussion."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4168170,
    "end": 4169610,
    "text": "Council member McQuillan."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4172570,
    "end": 4185210,
    "text": "I have questions for you, Mr. Lukeman. Can the city attorney confirm for the public that the City of Fairfax operates under a council manager form of government and that the appointments to boards and commissions are made by the City council as a body?"
  },
  {
    "speaker": "City Attorney",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4186490,
    "end": 4188490,
    "text": "Yes, that is clear in the city charter."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4188490,
    "end": 4198090,
    "text": "Thank you. Can the city attorney confirm that interviews and deliberations on applicants occur in closed session and the final appointments are voted in open session at a regular meeting?"
  },
  {
    "speaker": "Councilmember Stacy R. Hall",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4198490,
    "end": 4198970,
    "text": "Yes."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4199290,
    "end": 4211290,
    "text": "And can the city attorney also clarify for the public whether any individual members recusal on a particular appointment does or does not change the council's collective authority to proceed under its established appointment procedures?"
  },
  {
    "speaker": "City Attorney",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4212210,
    "end": 4214050,
    "text": "Could you restate that question, please?"
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4215330,
    "end": 4228530,
    "text": "Whether any individual member's recusal on a particular appointment does or does not change the council's collective authority to proceed under its established appointment procedures, an individual's recusal"
  },
  {
    "speaker": "City Attorney",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4228530,
    "end": 4246180,
    "text": "simply changes the number of votes required. And it also. Even if a majority of council members recuse on an item, it doesn't affect the quorum for purposes of voting on an item. So it just simply becomes the remaining members vote on the particular appointment."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4246820,
    "end": 4247380,
    "text": "Excellent."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4247380,
    "end": 4266820,
    "text": "Thank you. The city. City's own materials say appointments are made by city council and coordinated through the city clerk. I'm asking that we simply restate the city's own rules on the record. That's all I'm doing. I also want to. I do have a few more questions. Sorry, I'm kind of going through here."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4274360,
    "end": 4274640,
    "text": "Okay."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4274640,
    "end": 4276560,
    "text": "I asked those. Just double checking, making sure."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4276560,
    "end": 4289400,
    "text": "My notes here. Sorry."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4289400,
    "end": 4292480,
    "text": "I'm just going through my notes because I knew this was going to come up."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4292480,
    "end": 4294520,
    "text": "May I read? May I ask a question in the meantime? Is that okay?"
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4294520,
    "end": 4295080,
    "text": "Council member?"
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4295240,
    "end": 4296520,
    "text": "Yes, of course. Go for it."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4297520,
    "end": 4314160,
    "text": "Council member Hardy Chandler, to my recollection, each time we have met to discuss this board and commission, you have recused yourself. Okay. So every single time we've had discussions and conversations, you have, on your own, chosen to remove yourself."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4316080,
    "end": 4366000,
    "text": "That was without clarification that I could have input on the other candidates having Received that clarification. I want to exercise that I see an appointment for a four year term extending through April 14, 2030, and serving as a representative to Parks and Recreation Advisory Board as separate from the other appointment, which I recused myself from extending through September 30, 2029. These are separate independent appointments. If these candidates were coming up for candidacy separately, if that was without the second one, I would certainly have a voice on the other position. So in my opinion, with this new information, I do want to have input on this other position, which is a separate appointment."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4366240,
    "end": 4392050,
    "text": "Okay. And I understand your perspective on it. I happen to disagree. And I think that if a spouse or family member serves on a board or commission, it makes perfect sense to be recusing. And clearly the state code seems to support that. I did have one other question in the meantime, before I pass the floor back to Council Member McQuillan. Mr. Lupkman, are you aware of any times in which the mayor has voted on a Border Commission nomination in the"
  },
  {
    "speaker": "City Attorney",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4392050,
    "end": 4401690,
    "text": "20 years I've been city attorney? Well, I'll turn it around by saying my experience has been that most appointments to boards and commissions tend to be close to unanimous by the body."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4402570,
    "end": 4403130,
    "text": "Okay."
  },
  {
    "speaker": "City Attorney",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4403370,
    "end": 4404490,
    "text": "That's the fair statement."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4405210,
    "end": 4415470,
    "text": "So I think we can inter that to how we would like it to. But it sounds like in most cases a mayor's vote would not be needed. But is the charter wording such that the mayor does have a vote in"
  },
  {
    "speaker": "City Attorney",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4415470,
    "end": 4453210,
    "text": "that the mayor can vote on procedural aspects related to the appointment. So, for example, deferring action on an appointment, those type of things are perfectly legitimate. I have always taken the position that the appointments to boards and commissions legally is the province of the city council. It is also true, and people throw the word tradition around. It is also not an incorrect statement how it was characterized previously as to previous actions by previous councils and mayors. But that is not a legal requirement. That is just simply an agreement among the parties."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4453370,
    "end": 4475460,
    "text": "Okay. So I think if we have hired you as our attorney and we tend to consider you an expert in all things city legal, and we thank you very much for your service, frequently we should understand that you are making a statement that says that the mayor legally is not entitled to vote on these things and that it has been counseled that votes on boards and commission nominations."
  },
  {
    "speaker": "City Attorney",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4475780,
    "end": 4480260,
    "text": "Yeah, I'm not making a legal statement on the mayor voting. I'm. I didn't write the city's charter."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4480340,
    "end": 4484180,
    "text": "I understand. But we rely on you to interpret and to give us your best legal opinion."
  },
  {
    "speaker": "City Attorney",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4484660,
    "end": 4492900,
    "text": "Absolutely. And it's also True that on matters such as recusal, et cetera, those are the province of individual members of this body and the mayor."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4493300,
    "end": 4493780,
    "text": "Yes."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4493950,
    "end": 4494150,
    "text": "Okay."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4494150,
    "end": 4496030,
    "text": "I will give it back to Councilmember McQuillan now."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4496030,
    "end": 4529660,
    "text": "No, actually, I give it back to Councilmember McQuillan because I'm running this business meeting. So thank you. So let me clarify. Let me clarify. By saying, when I said vote, I don't mean vote from the dais. What I'm saying is, when discussions were held in closed session about appointments to boards and commissions, there were seven people, if there were even seven people in the room who gave input. This is not about my voting from the dais for this. This is about the body acting like a body. What a concept. And I am still running this meeting. So, council member McQuillan, would you like to make further comments?"
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4529820,
    "end": 4559520,
    "text": "Yes, please. Thank you. What concerns me is the imperance, the appearance problem. If a member properly recuses from a specific appointment because of a spouse's candidacy, but then, after learning the outcome, seeks to delay the process because the full result is not what she wanted, that creates an appearance of personal influence over a public appointment. Even the appearance of that is damaging, and that's my concern. Thank you,"
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4561600,
    "end": 4563040,
    "text": "Council Member Hardy Chandler."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4563440,
    "end": 4584310,
    "text": "I think that would be an issue if I had a concern about my husband being appointed. So in my absence, my husband was appointed, and that has nothing to do with me. I want no input on that, whether he's appointed or not. What I want input on are the other candidates for the other positions, just as I have input on the other candidates for other commissions."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4586150,
    "end": 4587430,
    "text": "Councilmember Peterson."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4587430,
    "end": 4709460,
    "text": "So, as a matter of practice, in this case, which is common, we have more than one slot open on a board and commission. We have multiple candidates, and it is not uncommon for the council to exercise flexibility and discretion on where those appointments fall among those set of slots that exist. This has happened frequently. In fact, it has involved councils actually appointing applicants to other committees than they had actually applied to. So this is certainly within the discretion of the council to decide who is appointed to which slot. The practical reality, again, is that it is very common to have multiple applicants for. For one or more slots. As a consequence of that, in this case, and anything like it, we have a candidate, an applicant, who is the husband of a council member who has applied for two different slots by virtue of applying in this area, and the council could be making appointments for that person in either of those slots. And as long as that applicant is still an applicant, and as long as the slots either of them are still open, then the dilemma that we have here is we have a spouse making an appointment of another spouse. And that, to me, is not just something that appears improper. I think this is an ethical issue, and I can't imagine that this council would want to exist without proper conflicts of interest procedures to prevent this very kind of thing from happening. And we see that state law intends very clearly to avoid this, and very clearly for localities to follow this. Whether or not we've taken the step we need to in codifying this is another matter. I believe we should. But this clearly is something that fits within the realm of our practice, that we now find ourselves being faced with a conflict."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4711460,
    "end": 4719940,
    "text": "We have a motion on the floor. It's been properly made and seconded. Let's go to a roll call vote to see if we have votes."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4720320,
    "end": 4724800,
    "text": "On this dais to move that motion forward. Ms. Shinneberry."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4725760,
    "end": 4728880,
    "text": "Council member Amos. Aye. Council Member Hall."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4731440,
    "end": 4732160,
    "text": "I'm sorry."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4732160,
    "end": 4733640,
    "text": "Read the motion, please, that we are"
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4733640,
    "end": 4734480,
    "text": "voting on right now."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4735680,
    "end": 4736560,
    "text": "So, Hardy."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4736960,
    "end": 4737440,
    "text": "Yeah."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4740320,
    "end": 4740720,
    "text": "12."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4740960,
    "end": 4741520,
    "text": "Okay."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4742240,
    "end": 4742680,
    "text": "Okay."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4742680,
    "end": 4743520,
    "text": "Hardy Chandler."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4743760,
    "end": 4744680,
    "text": "Aye. Okay."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4744680,
    "end": 4745840,
    "text": "Council Member Peterson."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4746050,
    "end": 4753490,
    "text": "No. With a caveat to Just the questions were not finished. Here's some other important details we didn't get a chance to ask about during this process."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4754850,
    "end": 4755890,
    "text": "Councilmember bates."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4756930,
    "end": 4757410,
    "text": "Aye."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4757730,
    "end": 4761970,
    "text": "Councilmember McQuillan. No. Okay. Motion failed three to three."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4762050,
    "end": 4765010,
    "text": "And we are going to move on to the public hearings."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4768210,
    "end": 4791470,
    "text": "The only public hearing tonight is for the FY27 budget. This is the third and final public hearing of the proposed FY27 budget the City Manager presented on February 24, 2026. I had two speakers sign up prior to the meeting. After I call those two speakers up, if there's anybody else in the room that wants to speak on the budget may come forward. So the first speaker is Douglas Stewart."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4799310,
    "end": 4935080,
    "text": "Good evening. So, as I mentioned in my previous comments, my wife and I have lived in Fairfax City for 22 years. Our son's a proud graduate of Fairfax High. And the city provides an exceptional level of public services and education at a lower tax rate than most nearby jurisdictions. But I think one area where we need to improve is reducing our energy costs. The cost of electricity is increasing significantly and fuel costs for vehicles are, as we know, very volatile. This has consequences both for our public buildings and fleets and for city residents and businesses just in our one household. It takes some work to keep track of our utility bill and identify where we are spending too much and could save energy. Now imagine that multiplied by hundreds, if not thousands of different utility accounts that a complex entity such as our city needs to manage. Who is keeping track of these costs and looking to realize more efficiencies and savings? Solar is now the cheapest, cleanest, and fastest to deploy energy source available in Virginia. We should be using solar for more of our public operations and buildings, including our schools. The city has a green building policy that can drive more energy savings both for our public buildings and for new private development. But without dedicated staffing, we can't put it in place. I think a dedicated energy manager can save the city significant energy expenses above the cost to fund this new position. They can also report on the savings so that you as a council and we the citizens know what we are saving and what we could do better. Beyond this, an energy manager can also help the city secure more outside funding from grants and connect with financing instruments that will support the upfront costs of new solar for private developments. We can't hold developers to building higher performance buildings without the energy manager to implement our green building policy. And those higher performance buildings will save our residents money in the form of reduced utility bills. So to conclude, I would urge inclusion of a full time position for an energy manager in the city budget. Thank you."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4937560,
    "end": 4939160,
    "text": "Our next speaker is Jennifer Rose."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 4951970,
    "end": 5136160,
    "text": "Good evening, Mayor and members of Council. Jennifer Rose, Executive Director of the Central Fairfax Chamber of Commerce. Thank you for the opportunity to speak and for the significant work by Fairfax City staff that has gone into developing the fiscal year 27 proposed budget. We recognize the real fiscal pressures the city is managing, particularly increases in school tuition and debt service, and we appreciate your commitment to maintaining services without adding new full time equivalent positions. From the Chamber's perspective, I want to focus on one key issue ensuring that Fairfax remains competitive for small businesses while making necessary revenue decisions. First, the proposed meals tax increase from 4% to 4.5%. We understand the goal of diversifying revenue. However, a meals tax is in practice a single industry tax. It places the greatest burden on restaurants, many of them small, locally owned businesses. We know this. They operate on thin margins and on the customers who support them. Restaurants are not just another sector. They are a cornerstone of our local economy. They drive foot traffic, support tourism and contribute to the vibrancy of Old Town and our commercial corridors. And I would like to point out for the first time in more than 20 years, our restaurants are finally on a level playing field with Fairfax county restaurants. Now that the county's implemented its own 4% meals tax, we respectfully urge council to reconsider this increase or at minimum include a clear sunset and ensure that any new revenue is reinvested in ways that directly support the hospitality and small business community. Second, if additional revenue is needed, there are more balanced alternatives. The Chamber supports exploring visitor based revenue options such as aligning the transient occupancy tax with regional levels. If authorized by the General assembly, this approach brings in revenue from visitors rather than placing additional strain on local businesses and residents. Similarly, if B pole adjustments are considered, it is critical to protect small businesses. The city's current threshold of $10,000 is very low, captures many micro businesses. Any changes should include raising the threshold and phasing and increases to avoid unintended impacts on startups and small firms. Third, and just as important, we encourage you to protect economic development capacity. The most sustainable way to reduce long term tax pressure is not by increasing rates, but by growing the commercial tax base that requires continued investment in business attraction retention and critically, faster and more predictable permitting. If we want Fairfax to remain competitive in attracting and retaining businesses, we must continue investing in the systems and resources that support the growth. So our request is straightforward. Avoid disproportionate impacts on any one industry, pursue a more balanced visitor informed revenue strategy, and continue investing in the economic development efforts that will strengthen Fairfax over the long term. Thank you for your time, your leadership and your commitment to our community. We look forward to continuing to partner with you."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5138000,
    "end": 5142160,
    "text": "Is there anybody else in the room that would like to speak on the proposed FY27 budget?"
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5146160,
    "end": 5161420,
    "text": "Okay, I will now close the public hearing on the proposed FY27 budget. Budget adoption will be on May 5, 2026 beginning at 7pm Ms. Shinneberry, we"
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5161420,
    "end": 5168100,
    "text": "will move forward to second general public comment I had one person sign up prior to the start of the meeting. I will call them forward. Mary McDaniel."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5175700,
    "end": 5309860,
    "text": "Thank you. I'm Mary McDaniel, a resident of the Fairfax City and my comments tonight are unrelated to my role on the city's electoral board. I'm speaking in support of the Willard Sherwood center and I'm asking that the City Council advance this project. It's an essential facility for our growing city. I have attended a ton of open houses on this and have always supported the project. As I look at it, it seems very obvious that we should move ahead and I started thinking about why would you maybe cancel the project? And one might be that the services that are going to be covered are not needed anymore. But in fact the services are needed more now than 10 years ago when project Planning started speaking to a few of them the Daycare Center. Our population has grown and along with that is the need for child care public health services. Again. Larger population means more demand. On top of that, the federal government has significantly reduced spending on public health and plans to continue to do more. So states and localities have to step up community space. In the past 10 years, we have learned a lot about the importance of personal contact and mental health. You know, texting is fine for some things, but face to face communication is far more important, as is exercise. So the senior center is really critical. Something that doesn't get talked about much is parking. The Sherwood Center Parking center fills up when popular programs are taking place in the evening, so having a parking garage attached to the building would help solve that problem. I am well aware that this building would raise my property taxes. I've owned two houses in the city over the space of 35 years. My real estate taxes have never gone down the rate may have decreased, but the amount I paid always went up. And I understand that because every year the cost of living goes up. In my adult life, this consumer price index has decreased only one time. Hundreds of citizens like me have spoken for more than a decade in open houses about wanting this project. And we know that the city will need to raise taxes to do this and may need to sell bonds. This has been openly disclosed and discussed throughout the planning process."
  },
  {
    "speaker": "Councilmember Stacy R. Hall",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5310960,
    "end": 5352290,
    "text": "We've had a ton of experts weigh in from architects, building engineers, landscape people, and the dedicated city staff who have worked diligently to pack as much as possible into this site over the years. I've never heard a city council member campaign on the idea of canceling this project. And I don't think now that any of you did. What I ask at this point is this. You've heard from the experts about what can be put into this building and how it benefits the community. And you've heard the community speak about the wants that we have. I ask that you follow up on promises that have been made, advance this project and finance it as needed."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5355730,
    "end": 5359570,
    "text": "Is there anybody else in the room that would like to speak under the general public comment?"
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5362540,
    "end": 5364700,
    "text": "All right, I will now recess the regulator."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5364700,
    "end": 5365580,
    "text": "Hang on before you do that."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5365580,
    "end": 5374380,
    "text": "Excuse me, I have not recognized you, Councilmember Peterson. I am now adjourning the meeting to go into a work session. We will stay in the chamber."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5379420,
    "end": 5389270,
    "text": "Our work session item is discussion on the proposed FY 2027 budget. City Council identified topics. I'm going to recognize Daniel Alexander, our city manager, for the staff discussion."
  },
  {
    "speaker": "Public Commenter",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5390700,
    "end": 5442280,
    "text": "Good evening, Mayor and Council. To frame this discussion tonight will largely be a conversation around revenues and expenditures. It's not going to be the full picture. We've had some conversations up to this point. We have some moving items. We still have some things that we expect out of Richmond relative to their process. And so there will be some additional conversations around how those numbers are shifting. But I think for the most part, as where we are in the process, we're a good place to talk about some things that have come up regarding revenues and expenditures, answer some of the questions that you've asked around those items, and then prep us to move forward into a constructive markup session on the 28th and hopefully adoption on the 5th. So with that, I'm going to turn it over to our Assistant city manager and CFO, Mr. Martinez."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5444030,
    "end": 5853850,
    "text": "Thank you, Mr. Alexander. Mayor, council this evening, if we can go to the next slide. Ms. Riddle, tonight's presentation is intended to provide a high level update on the FY 2027 budget, specifically focusing, as the manager stated, on revenues and expenditures assumptions. As a reminder, this is not the final iteration. Staff will return on April 28th with more detailed scenarios and options for council's consideration as we move toward finalizing the budget. We'll begin with revenues listed on the sheet that's on the screen. And before you are previously discussed, additional proposed changes of three revenue sources, two within the B poll and one on ToT. These three items were introduced earlier this evening and represent a potential maximum increase as communicated in several respective budget memos. The associated revenue from these increases are listed on the right side. Additionally, the Commissioner of the Revenue, in collaboration with the Budget Director, reviewed and revised upward the anticipated personal property revenue projection originally budgeted in the proposed FY27 budget by an additional $400,000. Let me be clear that this increase does not represent any change to the personal property tax rate and is solely due to a revised forecasting and modeling. Next slide Turning to expenditures, there are a few important updates to highlight. First, health insurance costs have increased beyond our original projections. Specifically, we are now projecting an additional 5.5% increase above the initial 8% forecast, largely driven by higher than anticipated claims activity. In response, staff is taking a proactive approach. We are meeting we have a meeting scheduled this Friday with our Insurance representative to explore strategies to help curtail future cost increases, including evaluating plan design options and potential rebidding of our insurance contract. Secondly, you will see personal expense savings reflected in the updated numbers. Approximately half of these savings result from a review of current staffing levels where we are prioritizing the reallocation of existing vacant positions rather than adding new FTEs. This approach allows us to meet operational needs while maintaining fiscal discipline. The remaining savings are anticipated from projected employee retirements and turnover which will increase the current budgeted vacancies savings factor not reflected on the current sheet are two additional items still under evaluation. First, there is a payment to vdot. Staff is currently assessing the most appropriate structure with a preliminary approach that would phase the payment approximately 1/3 in FY27 and the remaining 2/3 in FY28. Second, we are considering a modification to the timing of school related debt rather than committing the full 1.7 million in FY27, the proposed approach would include only 600,000 in the baseline budget through a contingency within the assigned fund balance, the remaining 1.1 million deferred for future consideration. This approach is intended to preserve flexibility as we monitor potential changes at the state level. Specifically, current Virginia Senate bill amendment language would authorize the 1% sales tax dedication to school projects contingent upon voter approval through local referendum. Importantly, those revenues would be restricted to construction or major renovation projects and could not be used to supplant existing local funding that has already been budgeted or appropriated. That is the key language and the change that is in the current draft language. The General assembly will be reconvening a special session and hopefully we will Know more by the end of this month or the beginning of May. Next Slide Fund Balance really quickly provides a high level look of our fund balance status. This is intended as a preview and a reminder of more detailed analysis that is regularly presented during our quarterly Financial review with Councils that our Budget Director does. Our next quarterly update is also scheduled for April 28. That will happen prior to the last budget work session. As part of those reviews, we not only walk through the fund balance levels, but also provide an updated snapshot of our current fiscal position, revenues versus Expenditures as well as a refreshed five year financial projection. And then lastly, next slide. Thank you, you're probably used to seeing this. We just want to reiterate. The last slide outlines our budget calendar and where we are in the process. At this point we are more than halfway through the FY27 budget development cycle and we are entering the phase where Council direction becomes critical in shaping the final document. I also want to highlight one upcoming engagement opportunity. The Engage Fairfax Fiscal Year 2027 Community Budget Exchange is scheduled for April 16th has been updated. Let me say that one more time has been updated to reflect a revised access link that will now be held via Zoom instead of teams. We were notified by Microsoft Teams that there was a bug so we had a pivot very quickly and as of this afternoon a few hours ago, the communication staff has updated all links and all distribution lists with the new Zoom updated Link. Looking ahead, April 28 is a key milestone with multiple public hearings and our final work session where staff will present again refined options and draft changes for Council deliberation. In closing, tonight's update is meant to keep Council informed of where things stand today. We will return on April 28th with more detailed analysis, refined assumptions and actionable options to to help guide your decision making. Happy to answer any questions. Councilmember Amos thank you."
  },
  {
    "speaker": "Councilmember Billy M. Bates",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5854090,
    "end": 5896570,
    "text": "I know I submitted a number of questions prior to going on my trip and I know you're still working on those and I'm assuming generating response to circulate to everyone or to me, whatever works best. The only other question and follow up I'd like to discuss is specifically, I know that the Chamber just brought it up. I would like to have a more serious discussion on adding a sunset to the increase in the meals tax contingent on the 1% being activated. And I may be misunderstanding this, but Once we get the 1% for school construction, essentially restaurants will be at 5.5% versus 4.5% at least for the time being until they're paid off. Is that correct."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5898730,
    "end": 5900010,
    "text": "It's going to depend on the."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5900160,
    "end": 5927990,
    "text": "Current language. The last language I saw, I think on meals tax and looking at the budget director because I think she showed it to me, the language may not be applicable to meals or, or restaurant meals for the additional 1%. That is still something that is being evaluated. We won't know. And I think that's sort of the biggest predicament that we're in right now is there has been no final determination by Richmond. So we're trying to be as adaptive and as prudent as possible."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5928310,
    "end": 5953890,
    "text": "Yeah, I know we're still waiting for legislative updates, but once we get that clarification, if that is the case, I think it's worth a follow up discussion. Thank you. Council Member Peterson, you went through a number of specifics and I don't think we had numbers on slides in front of us. Is there going to be a listing that we can refer back to with all of this?"
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5955170,
    "end": 5982480,
    "text": "Definitely. So I think this traditionally is being uploaded the next morning. So tomorrow morning. And then as mentioned on April 28, we will present at least four to five options or scenarios. Very similarly what we did last year to council. It's my understanding that we also have meetings sort of scheduled one on ones. So I think starting next week with council to sort of walk through some of those potential scenarios. But definitely have it in a public forum on the 28th."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 5984240,
    "end": 5998000,
    "text": "And so. Thank you. To put this in context then, you had a series of numbers. Are these numbers tied to any particular scenario at this stage?"
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6000640,
    "end": 6044040,
    "text": "Not 100%. So what was displayed in some of the other slides, the revenues and the expenditures are what we know of right now. The most traditional way that we've displayed this is the budget change sheet that will be a part of it. That's sort of the debit and the credits. The changes that have that are now known as of when the manager proposes budget at the end of February. We're keeping track of that. We're not anticipating any other changes between now and the end of May other than the two that we've identified that were not listed on here. The VDOT repayment and then the potential school deferral on debt. Besides that, we're trying to formulate an option and scenarios for council."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6045480,
    "end": 6065340,
    "text": "So when we get back together again April 28, you'll have scenarios for us to discuss and we will have a scenario then that this information will be factored into which will be at least one of the scenarios. The manager's proposed budget, is that correct?"
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6065340,
    "end": 6065900,
    "text": "Correct."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6066140,
    "end": 6079660,
    "text": "Okay. And then we will have additional scenarios that you've been developed, able to develop based on further work that you've done on all of these items, including revenue and expense improvements that you've been able to identify. Is that fair?"
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6079820,
    "end": 6080779,
    "text": "Correct, Council Member."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6080779,
    "end": 6084540,
    "text": "Okay, thank you very much, Council Member McQuillan."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6085500,
    "end": 6092460,
    "text": "Okay, sorry. Going back to what you stated prior to Council Member Amos question. Could you please repeat that?"
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6095300,
    "end": 6102180,
    "text": "I think you're referring, Council Member, to the potential 1% sales tax for school capital."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6102580,
    "end": 6245210,
    "text": "Okay. Is that what. Sorry, I couldn't hear the whole thing. So I was just needing a little bit of clarification on that. Thank you. I did want to mention to my council colleagues that I am the. I am the representative of the Food and Agricultural Regional Membership Policy Committee Farm. And we recently had a meeting in which. And I just want to share a few little updates and facts. This, this supports my position on the meals tax. You guys all know where I stand on that. I've been really open about that. National Restaurant association reporting this year says that 42% of operators were not profitable and had limited ability to raise menu prices further in 2025. It matters because restaurants do not absorb taxes, inflation, labor costs, inc. Insurance, rent and supply volatility in separate buckets. It's all in one. It all hits the same operating margin. Consumers are already paying more. The national CPI shows food away from home is up 3.8% over the year and full service meals are up 4.3%. That's their pricing. In the Washington region, food away from home went up 3.7% over the year with overall food prices up 4.4.5%. So this is not happening in a low inflation environment for food. Also, the Virginia gas prices being elevated. AAA is showing that Virginia's regular gas average is about $3.99 per gallon. And AAA's national reporting shows fuel prices climbed sharply in early April amid high crude prices and geopolitical disruption. That's affecting the grocery stores. It's affecting everyone in the food industry. We're seeing an uptick of food insecurity, especially among our lower middle class families. So please keep all of this in mind when we're discussing increasing the meals tax, because it doesn't. It's just not one meal. This is several meals. People eat hundreds of meals over their lifetime or over a year. So when we're talking about increasing the tax, yeah, it sounds like a small amount, but it's really hitting our restaurants hard and we like to brag. We're often celebrating the city's restaurant scene as unique and defining these cultural strengths. Just recognize that this is impacting those businesses when we do this. That's all I wanted to share. Thank you, Council Member Hall."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6245770,
    "end": 6490010,
    "text": "Thank you. In anticipation of the conversation about bpol, I reached out to two different people. One specifically with a very large car dealership who does repairs and car sales. And then another person that I reached out to is a professional in the legal area. So the. I think they're both. The car tax was or the car B poll conversation was more about the lesser of two evils of real estate taxes versus BPOL tax. The conversation that we had focused very heavily on the fact that the majority of the B poll, I actually didn't realize we collected it on car sales. I thought it was only on the service portion, but that is passed through to purchasers. So while that will have an impact on car dealerships and on service centers, the impact would be likely less than an increase to the real estate taxes. I did have concerns after speaking with multiple people about the rate and what we were discussing as far as the professional services. And I will be the first to say I was the one who asked these questions. And I was reached out to people intentionally to get additional information. So just to say that what they were suggesting was that unfortunately, people really might pick up and move to the county if we go from the $0.40 to the $0.48 or 0.48, whatever the phrasing is. And that, you know, the county, I think, is at 0.31 31 cents. So there was some concern that an abrupt hike like that would suggest that people are leaving or will leave in the coming years. This person also had some very interesting information with regard to the meals tax and specifically said that there's a restaurant that has a chain here that also has one near us in the county. And. And he said that he purposely doesn't go to the one in the city because it didn't because it had the 4% meals tax. So I think he was fairly shocked when he went to the county counterpart restaurant and found that that meals tax was there now. So he said, I guess I can go back to the local city one. However, what he did suggest was that maybe we consider reducing the meals tax rate to 2%. And I understand that will have financial impacts and I would also just like to have staff's thoughts and feelings on this. But would that be an opportunity for us to capitalize on the fact that county people are unhappy with this? It could be a huge promotion that we could do in combination with the chamber of commerce, all the restaurants, you know, maybe we talk about trying it for six months or a year or something and see how we are doing with it. I would be open to having this conversation if it's supported by others on Lada, to at least entertain it and see what staff thinks. I think, you know, we got an email from a woman today. I think everyone got it about, you know, she went to the grocery store and she bought a prepared chicken and, you know, the tax now was 4 cents higher than it was before. And I mean, she said 4 cents is not a lot, but 4 cents consistently all the time felt like a lot. And so she, you know, doing the correlation of just what that half cent would be. So, personally, I hate the meals tax. I've always hated the Meals tax. I'm happy the county now has one because I think it makes us comparable. I also do recognize that in order to generate that 1.25 million that the meals tax increase of a half a cent, sorry, half a percent, will bring in, would also require, I believe it's 1.417 cents on the real estate tax rate. So I understand it's a one or the other or both. But these are just some ideas and some thoughts that I would like to hear about. The other thing is, you know, everyone I talk to, when I talk about the lesser of two taxes or what if we only had to raise it $0.01, all they continue to ask back is, why are we not reducing our expenses? And so I'm happy to see some of the slides and things that you're showing forth here that are talking about reductions, but I think it's a very valid question. So I don't know."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6490160,
    "end": 6573140,
    "text": "Expect a response. Now, I do have specific questions that I would like responses to, but I wanted to just give you some overall thoughts. I personally am very interested in seeing ways that we can try to bridge the gap between what the EDA was receiving and then is no longer receiving. I personally would really like to see the Renaissance program reinstated. I know I was the one, I believe, last year who suggested that maybe we put a pause on it. And it was truly meant to be a pause. It was not meant to be a removal from future consideration. I did reach out to the staff counterpart today and asked if it were to be reinstated, how many loans would we be able to service and get that similar information that we were provided with last year, which made me more willing to consider putting a pause on it. Now my questions are going to come in. So the conversation about the 6. $600,000 for the schools versus the 1.1 deferred. I understand or I don't understand. I see we have school board member Sarah Kelsey here as well as our superintendent Dustin Wright. And I understand that there was a meeting last night with the school board. I didn't get a chance to watch all of it. Are there. Was it a good conversation? Are the schools in favor of this? I'd like to just hear from the schools, if that's possible. Not to put you on the spot or anything, but you're here, so you probably expected to be brought up."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6574500,
    "end": 6577860,
    "text": "Certainly. Mr. Wright, if you would like to add something."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6580900,
    "end": 6581460,
    "text": "Thank you."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6588820,
    "end": 6616310,
    "text": "Thank you, Mayor Reid. And good evening to the council. Council member Hall, I was. I'm here to observe and listen, but I'm happy to answer your question that you just posed. The conversation last night was around our elementary school capital projects and the current state of them and, and the path moving forward. None of it was related to the proposal that you heard this evening? We were not aware of that proposal at that time."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6620390,
    "end": 6628710,
    "text": "Thank you. Okay. I thought that was being discussed with the schools prior to our conversation tonight, Mr. Alexander."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6628710,
    "end": 6644110,
    "text": "Yeah, so we. We have talked to council about it up to this point. We have talked today with them about it. And so I don't know the degree to which Mr. Wright has socialized that with the board yet. It is."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6644190,
    "end": 6644550,
    "text": "We're."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6644550,
    "end": 6657580,
    "text": "We're calling it an option in respect to, I think, the council and also in respect to schools. And so it's going to like the other things that we brought up tonight, beg some further conversation around that."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6658380,
    "end": 6663980,
    "text": "Okay, thank you. Sorry to call out the very uncomfortable elephant in the room, but I was just curious where schools were on this. So thank you,"
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6666220,
    "end": 6735270,
    "text": "Councilman Peterson. I wanted to just build a little bit on some of the inflation related information that Councilmember McQuillan provided because it is an important part of the inflation equation, but it's only a part of equation. And just a note. We heard some testimony tonight about the concern about energy prices. We know from earlier information provided by staff that Dominion Energy has notified us we should be expecting a 32% increase in electricity. We know also that we're looking at a 13% increase in natural gas. So on the energy front, those are two sources that serve what we call the stationary source sector, buildings, facilities, et cetera. And it affects the city's own budget. And I understand that our projection on increased electricity costs, if that materializes, will knock on the door. $400,000 incremental expense. Is that a correct recollection of the impact of that cost increase?"
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6736550,
    "end": 6754550,
    "text": "It is based off of the assumption that that rate increase is going to hold. That has not been confirmed. Dominion put that out. It is my understanding that that will more than likely not happen. You will have a more realistic increase based off historical Trends, probably around 10 or 12%, not 35."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6755350,
    "end": 6899550,
    "text": "That would certainly be good news if that happened. I know there's a lot of concern that those rates are going to go up and that the unexpected changes will be on the upward side. But we're not there yet. It's good to know. But clearly energy is up. I would just note also that healthcare expenses are up and that maybe the highest and fastest rate of inflation for any household expenses that we experience. The latest that I saw for unreimbursed healthcare expenses, it's running an increase of 21.5% this year. And there's a big caveat there because Obamacare has not been refunded yet and it's not clear that it will be. So for people who are dependent upon that and the reimbursements associated with it, this is a big load for an average family of four in the city of Fairfax. The mean right now is looking at about $27,000 a year. You translate that out with other household expenses, including the ones we just heard about, and it's really saying that 150,000 median income is what you've got to have to swing it in terms of dealing with, with this cost load. So healthcare is a really big one. There isn't much, if anything, we can do about that except to stay well and get all the help we can doing that. But there are things we can control and Those are our property taxes, our real estate taxes, and other fees. So it's not surprising that people, as we've heard, are hoping that we will do everything we can to manage that cost agenda, recognizing that there are things that are changing in a major way that we cannot control, but there are things that we can control. To switch gears and go to the Renaissance housing Program, just out of curiosity, I believe, based on prior conversations and some of the staff consultations on housing issues of a variety of types, we're taking a really hard look at how we are approaching our housing programs here in the city. And that's not limited to affordable housing, but it's looking at the sector and what to do with that. As you if and as you come back with thoughts around any of our housing programs, but including the Renaissance housing program, I'm wondering if you might be able to think through what a slightly more integrated approach to something like the Renaissance Housing Program might be. Given that I know you're looking hard at what an integrated approach to this housing area maybe might look like in the future, I'm wondering if that might be a possible thing framed."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6899550,
    "end": 6928260,
    "text": "Well, Councilmember, that certainly is part of the way we'd want to look at it. As you say, an integrated program. I don't believe that we're prepared to obviously introduce that as part of the current plan, but certainly should be, I think, should be part of the way we look at our complete approach to our housing. So that certainly will be something that we bring back to council as we discuss everything related to housing. So I think you framed it exactly the way we're looking at it."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 6928340,
    "end": 7046890,
    "text": "Okay. And then just another note that I think we've talked about before. We are not there yet in terms of going through the efficiency and innovation audit that last year we passed and requested. That is going to happen sometime in the not too distant future, we hope and expect. But I think the point is that we're not there yet in terms of knowing what potential that might have in terms of freeing up financial efficiency here. So we don't have the advantage of plugging that in now, but I think we have something to look forward to. So just to note that then on the, just to take a step back on the energy issue, there is an enormous amount of interest everywhere right now in getting ahead of the curve on that issue. And we've heard about it here. This is something that is pretty much everywhere and for very good reason. The load growth issue is not going to go away. It's a very big one. I think the real challenge that we have is to address this really rapid runaway train we call load growth, but to do it in an environmentally and economically friendly manner. And I think there's a way to do that. This happens to be my profession, so I know a lot of people are involved in this right now. But I think as we hear back from you about your thoughts on how the city can approach its part of this issue, it would just be great to know that as we're doing that and we're looking through the energy lens, we're looking at cost savings, we're looking at economic gains from doing this, and we're looking at ways in which that can be done in an environmentally friendly manner, because I think that's the win win everybody is looking for. And I know we've probably gotten a head start on that because we have talented staff that are looking at that. But that thematically is, I think, where really all jurisdictions are kind of heading this way. Thank you, Councilmember Hardy Chandler."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7050330,
    "end": 7078660,
    "text": "And I hate to ask for data that I didn't previously ask you to prepare, but I'm just curious if there is just historic knowledge of sort of the, for lack of a better word, sort of restaurant migration sort of behavior historically when there have been changes in the meals tax. I might not be recalling this accurately, but I believe that there was sort of some landscape."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7081600,
    "end": 7102320,
    "text": "Multi jurisdictional information that was previously presented. I'm just wondering if, in addition to the anecdotal conversations that we might have with residents, what sort of the trends show in terms of what actually happens in the. What actually has happened in the past when there have been those changes."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7103920,
    "end": 7229800,
    "text": "I'm going to try to go off of memory. Council member. We, we did present something at a work session with some historical data that actually compared the city of Alexandria, who has a 5% meals tax compared to the city. They've had it for about 20 years, so very similar to our 4% as well. Additionally, in that presentation there was an actual number of increased restaurants over the same 10 to 15 year period in the city. So not necessarily a migration out, more of an expansion. I want to say it was on average two and a half or three and a half per year that we increased the restaurant count between the timeframe that we looked at 10 or 15 years. It was actually an increase, a net increase. Here goes. Excellent. Thank you, Ms. Riddle. So go to the next couple of slides and you can actually see the comparison. I don't have my glasses. Here we go. There you go. Go back one. There you go. So on there over the 20 year time frame, 2016 to 2025, a net increase of 59 restaurants or about 30% from where we started on average. Looking at. I can't read it from here, sorry. 3% per year. About 7U. Yeah, 7U per year increase. So we are seeing an increase overall. I think a lot of that has to do just with the work that our economic development office does. People want to move into the city. Also on the left hand side, it does show that about 3% is sort of past, through or back to the restaurants while they file their timely receipts to the city as well. So over that same course time frame, over $2 million was given back to these businesses as a form of collecting the tax on behalf of the city."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7231800,
    "end": 7291720,
    "text": "I'm impressed with how you had that available. So thank you very much. Shifting gears a little bit, the Renaissance Housing program. I believe that there was comment earlier about revenues coming back to the city because of property improvements. I'm also curious about whether or not there is flexibility in terms of. I'm not sure if the program's parameters allow flexibility to have input on some, some targeting around or developing matrices for who gets those loans. And if that hasn't been the case, do we have the flexibility to have input on how that might serve some of our longer term goals a little bit better or are the Program's parameters more rigid."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7292680,
    "end": 7351930,
    "text": "Excellent question, Council Member. And unfortunately, the Renaissance Housing Corporation is its independent body. So it does not directly fall under the city. It receives almost exclusively all its generating revenues or funds from the city. When we do fund them, there are their own independent parameters of how they, how individuals would qualify for a loan, what those qualification standards are in the sense of disbursement. They have their own limitations. To me, it would make sense that if the city is providing the majority of the funding that we may, if council so choose and if the city attorney would help, we could probably create an agreement to sort of put some structure on, maybe put some X number percentage to lower income housing or lower thresholds that would impact a different population."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7352810,
    "end": 7362810,
    "text": "So just to clarify, there is an opportunity for like an MOU process to find some common ground to meet the program's aims as well as the city's aims?"
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7362810,
    "end": 7364330,
    "text": "Potentially, I would say yes."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7364810,
    "end": 7368730,
    "text": "Good to hear. Thank you so much, Council Member McQuillan."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7369610,
    "end": 7370250,
    "text": "Thank you."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7370810,
    "end": 7440770,
    "text": "I too would like more discussion on the Renaissance Housing Program and to look into that to see what we can do since I think that really is a great program specifically for a certain group that does not seem to qualify for a lot else out there. I also just wanted to let you all know or update you on some information I just found from the Northern Virginia Regional Commission. This is about restaurants in Northern Virginia. It says that on average they've grown at an average annual rate roughly of 3 to 5% over the past decade. Decade. So that is what we've seen here. But it says that key factors driving that growth include rising household incomes, urbanization, expansion of federal and tech employment, which we know isn't expanding right now, increased demand for dining and suburban and mixed use developments, and growth of food delivery and E commerce. So I just want to, since some of those actually correlate to the things that I mentioned, gas prices, things that have increased the struggle for our small businesses and specifically our restaurants. I just wanted to provide that extra information. Thank you,"
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7443650,
    "end": 7444770,
    "text": "Council Member Hall."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7445010,
    "end": 7469220,
    "text": "Thank you. I had one question I forgot to ask. You mentioned that the health insurance had gone up another 5%, which I think was about 400,000, 300 and some thousand. Okay. And I know that I've asked this question before and I'm sorry, I don't remember your answer, but when was the last time that we did bid and look at our provider and look at our plan types and see are we offering things that are competitive?"
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7470420,
    "end": 7498370,
    "text": "It's been a while is the best answer that I can give Right now. But. But as I stated, we are meeting with our rep this Friday. And given the increases year over year, I think Councilmember Peterson also alluded to these are one of those inflationary increases that we can't necessarily control, but we're going to try to get ahead of it and then, if need be, really look at a potential rebid on that contract or break away from that plan and go independent."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7498770,
    "end": 7504130,
    "text": "And is that something that could be done in this upcoming fiscal year or are we locked into what we have right now?"
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7505090,
    "end": 7519810,
    "text": "We're pretty much locked in because we are just advertising what those rates are to the employees. We have open enrollment May 1, so we would probably have to wait an entire year before we could do that. But we would do that legwork now in preparation for FY28."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7520370,
    "end": 7556210,
    "text": "Okay. So I do this for my company as well. And so I know nobody likes to have two deductibles in a year, but what we ended up doing was we actually renewed January 1st instead of doing a July 1st renewal. So we had six months of one plan and then looped it back in. I understand we operate on a fiscal year, so that might create some challenges. But I would think that if it's attractive enough to consider a move, that we should potentially see what our timeline options are. My other question is, do we currently offer HSA compatible plans, like high deductible plans? We do."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7556210,
    "end": 7556610,
    "text": "We do."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7556610,
    "end": 7558650,
    "text": "And do we have the FSA options as well?"
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7558650,
    "end": 7559090,
    "text": "We do."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7559170,
    "end": 7563250,
    "text": "Okay. Do you know what our employees tend to choose?"
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7563250,
    "end": 7609570,
    "text": "Most of it varies. We looked at the plan. I'll look at Ms. Riddle if she remembers a little bit better. But we had those statistics. We just reviewed them again about a couple of weeks, maybe three weeks ago, when we got the renewal notices. I will say that given that the employer, the city, is not the only one taking some of this burden, the employee will also see a increase about 12%. That may actually move some people out of those higher plans into lower plans. So there may actually be some. When I say savings, lessen the impact of the 325 overall because they're going to see an increase in one plan while some other plans were stagnant. They may migrate to those."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7610050,
    "end": 7637330,
    "text": "Okay. I know we're not the overseers of all of the things. I just happen to have a personal interest in, you know, education in this area. If it's possible, if it's on our website or you could direct me to somewhere that I could see what we pay versus what the employee pays, just so I can see what that cost sharing looks like. Is that an option? I'm just curious, like, if we cap at a certain rate or, you know, what we cover for families and other individuals and whatnot."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7637730,
    "end": 7649730,
    "text": "The FY27 rates have not been released yet to employees, but 26, I believe, are on the website. And then I'm assuming you'll get it when 27 comes out as it goes to all employees."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7649890,
    "end": 7653570,
    "text": "Okay. My apologies. I wasn't really planning on discussing this in detail tonight, so I didn't look."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7653650,
    "end": 7670010,
    "text": "Yeah. No. And just to give you a little bit of context, we have just over 80% of our eligible employees that have our health insurance. The majority is with Anthem. We have two plans with Anthem. And then we are about, I think it's about 20."
  },
  {
    "speaker": "Councilmember Stacy R. Hall",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7670240,
    "end": 7672800,
    "text": "20 to 30% of employees are with Kaiser."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7672960,
    "end": 7673520,
    "text": "Okay."
  },
  {
    "speaker": "Councilmember Stacy R. Hall",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7673520,
    "end": 7674000,
    "text": "Yeah."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7674400,
    "end": 7710940,
    "text": "Okay. And I just have one other thing, and I know I've asked this a couple times previously, and I don't know that we've ever really come to a definitive yes or no. But I would like to suggest that when we either send out our final tax bills or when we send a response saying, hey, thank you for what you paid, I would strongly like to send a letter, not me personally, but the city, that says, thank you for paying your real estate taxes. Here are some of the things that you funded. And just make it a more of a personal impact opportunity to let people know that we know things are tough. So I don't know if that needs consensus from council or not, but that would be something that I would recommend to the Finance department. So thank you,"
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7713100,
    "end": 7714540,
    "text": "Council Member Peterson."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7715500,
    "end": 7802440,
    "text": "Just another quick note on the inflation thing. Maybe this is good news, maybe it's not. But the latest numbers I saw for the area on housing is that the price of housing has gone down a third of a percent this year. The forecast, Northern Virginia Realtors through the end of the year. End of the year, the high end of that is 1.9%. So housing is not one of the inflationary variables in terms of price that's going up, but we know that the cost of housing nonetheless is high. Going back to the. A little bit of the big picture here in terms of what we will see as we go forward. I know other council members have talked with you about this in terms of information that is of interest, but I. So I think one of the things that would be helpful is to the best of your ability to forecast forward five years to see what this trajectory looks like for the city in terms of expenses and revenues to, to avoid us being on a yoyo, this destabilizing pattern that has happened in the past where we've gone too far up, too far down and then had to play catch up and it's had a destabilizing effect. So if we can understand to the best of your ability what a smoother trajectory looks like and how we are consistent with that, so we could avoid the deviations in either direction, that would really be very helpful."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7802890,
    "end": 7819450,
    "text": "Yeah. The good thing is we're scheduled for third quarter, third quarter update, and within that, and I know, I've heard it from Councilman Rahal, too, of getting an idea of what we're projecting for the future. So the timing is right for us on the 28th to actually have that discussion in conjunction with our budget discussion."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7822010,
    "end": 7833100,
    "text": "Great. Great. Really, really appreciate it again, because we saw some roller coaster stuff in the past that I think we always want to try to avoid void in the future. Very helpful."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7835180,
    "end": 7836300,
    "text": "Councilmember Bates."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7839100,
    "end": 7926300,
    "text": "So as before, I support the proposed increase in the meals tax. It's much more modest than what was proposed last time around and at the end of the day, you know, certainly not something that we love to do. But even if we're able to make up that revenue through an increase in the B poll tax or fees and you know, some other revenue source that ends up being that much less the funding that we could use to perhaps further support our employees, our public safety employees who respond to emergencies that occur at the restaurants in the city. At the end of the day, housing is certainly more of a necessity than eating at a restaurant. You know, certainly some people, you know, don't have time to cook. However, there are, you know, frozen meals available at the grocery store, that kind of thing. So, you know, that's also kind of locking ourselves out of if we wanted to use part of that to alleviate some of the burden on our homeowners through the real estate tax rate. So it's something that I think I again want to encourage caution in ruling out as we go forward."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7929500,
    "end": 7930940,
    "text": "Yes, Mr. Martinez."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 7931820,
    "end": 8006400,
    "text": "Thank you, Mary. Just want to add a couple clarifying notes regarding the meals tax. A potential 2% reduction with each half percent being about 1.3, that's $5.8 million, almost $6 million that would be reduced or I'm sorry, that would be 1.3. So about over $5 million or the equivalent of almost $0.06, 5.8 cents on the current real estate tax rate. And I think Councilmember hall made that statement. And then additionally, just to clarify, and it's not on the screen per se, but when the manager proposed his budget, the we realized about $1.3 million in savings from available balances, specifically in operating CIP funds that came over to the general fund side and now we've shown another $400,000. So in totality the city has saved about $1.7 million in the FY27 budget. So not an insignificant amount given our size. Just wanted to make those two statements."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8008960,
    "end": 8022960,
    "text": "Council Member Peterson, am I correct that also in a prior session you indicated that we were looking at an unexpected increase in revenues of 2.7 million?"
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8025130,
    "end": 8049930,
    "text": "We were. In the second quarter financial review, the budget director displayed a 2.7, 2 point some odd million dollar additional revenue that has not been realized but is anticipated for FY26 with the understanding that that additional revenue would go to unassigned or assigned fund balance to sort of bridge the gap for FY27."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8051320,
    "end": 8052120,
    "text": "Excellent. Thank you."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8052120,
    "end": 8131320,
    "text": "Sure. So, speaking of the unassigned fund balance, we had encumbered funds in anticipation of a repayment to VDOT out of the unassigned fund balance for this year, I believe. But now that we've actually gotten the bill from VDOT for the repayment, we are. There is. There is a plan, I believe, that is going to be explored about how to repay that. And I bring this up because we have the budget event on April 16, and I think we need to explain how the $3.5 million is going to be paid back and the fact that while we had, you know, we had encumbered but not actually allocated that money from the unassigned fund balance, there's now a different plan. And I just think it's important before we get to April 28th for people to understand what that plan is for the FY27 and potentially the FY28 budget. So will there be a budget memo or how. How will you kind of put this up for the sake of transparency to the public when they come to discuss the budget on the 16th? How will that be rolled out?"
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8131640,
    "end": 8154820,
    "text": "Yeah, we have a process for those changes on a change sheet. Getting a nod in the affirmative. That's one element of a few elements that we've discussed tonight that we're going to need to work through, some of which we've have kind of pushed out just recently. So all of those changes from a revenue and expenditure perspective will be part of the scenarios that we bring to you on the 28th."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8156010,
    "end": 8170650,
    "text": "I guess my question is, will there be anything prior to the 28th that, you know, because we're having this event on the 16th and we have not discussed this since. It is a very new. It's a very new thing that just happened."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8172170,
    "end": 8234260,
    "text": "Yeah, I think that. And again, I apologize. Even with the school things a little clunky. Right. As we have talked about our options there. So from a revenue and expense perspective, these things are going to change as we move along. I think the 28th is our opportunity for us to have a full discussion on all of those and all those scenarios, which will include how we have given the Council options for decisions on how to approach that. What we've even brought up tonight are options and suggestions. Council may not like those and we may need to pivot. And so we'll have those discussions over the next couple weeks. I think Thursday is a great opportunity for the public to come out and ask their questions, be engaged and be responsive, and we'll certainly bring that back to you. You don't have that yet either. You have. We've had plenty of hearings and engagement, engaged platforms been up. We've done a lot of that. But that's another element that we're going to bring to you on the 28th and have a fully transparent discussion around everything related to revenues and expenditures."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8235550,
    "end": 8237710,
    "text": "Fantastic. Any council member. McQuillan."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8239070,
    "end": 8239550,
    "text": "Sorry."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8239790,
    "end": 8248990,
    "text": "I just want to thank you. I recognize that this is not a fun topic to discuss, and I'm sure it's not great unless you're Mr. Martinez"
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8248990,
    "end": 8249790,
    "text": "to work on it."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8250030,
    "end": 8260010,
    "text": "But I just, I recognize the amount of work you're doing, the amount of time it takes, you're continuing to do it with a smile on your face and."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8260160,
    "end": 8296130,
    "text": "And I can feel this isn't a fun process for anyone but you all. This is what you have to do for your job and you don't get to just decide you're done. So I just want to say thank you to all of the employees and staff that are working hard right now that are especially you all that are in the room because hearing the speed in which you're responsive to our requests about engage and the budget, I mean, we're throwing everything at you and you all are just handling it and rolling with it. And I just wanted to say thank you because I don't think we do that enough here and acknowledge how much work that is on you. So thank you."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8297490,
    "end": 8300970,
    "text": "Okay. Any other questions, comments, Council Member Peterson"
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8300970,
    "end": 8353120,
    "text": "Yeah, I just to build on. Great. Thanks to all of you. And I think the April 16 engagement is a very helpful and important time. I know we're all getting emails from people with questions and thoughts and what have you and I'm encouraging them to please try to attend April 16th or tune in because it's a substantive point in time where you can ask those specific questions and really get into the granular side of this. So we've got a lot of that still coming in that really indicates the desire for people to understand things at a specific level. So the event was really made for that purpose. And this is your opportunity. Again, I know you try to make it easy so folks can tune in remotely as well. I want to encourage everybody to take advantage of that. And just a note that I personally like zoom a lot better than I like teams."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8357120,
    "end": 8369360,
    "text": "Any other questions or comments before we. Okay, I'm now going to reconvene the regular meeting, Mr. Alexander, for future meeting topics."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8371330,
    "end": 8486570,
    "text": "Thank you. Mayor and council looking ahead to the 28th. We've had a lot of conversation up to this point and so you know, much of this will be focused on public hearings related to the budget. There will be some items not requiring a public hearing to include significantly the Blenheim Boulevard project. And then as we mentioned before, we will be talking about Willard Sherwood and the items that you've we've talked about tonight. And also on there is the consideration of bond resolution for general obligation bonds for the school project. Work session wise, we are again planning the third quarter financial review, so we're looking forward to that. And then as we've discussed the budget draft changes presented and deliberated on that night, also May 5th committed to budget in its entirety. And then looking ahead, moving forward into May, significantly, we'll have items on public hearings on financial costs, capital costs related to sewer system and bonds related to that. Also. We will bring back the noise discussion on that night. We'll talk potential options for detached accessory dwelling units and the council salaries will be back on that night. We've talked to council up to this point getting later into May about Wilcoxon Trail extension. So we'll bring that back to you with a presentation and that gets us into June. Happy to answer any questions relative to what we've discussed on these meetings or looking out through the remainder of the year at council's pleasure."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8489450,
    "end": 8530980,
    "text": "Councilmember Peterson on May 5, the very last item 7, considering adopting the budget, et cetera, et cetera. Is that a single vote that is on both budget and appropriations or are we doing a two step budget then appropriation? I think it's multiple parts. I confess I didn't go back and look at last year's script. So you caught me a little. That's why I'm asking. We can go back and look at the agenda from that meeting if you'd like. Okay. It would be wonderful just to have that nice and clear so we sort of know what we're doing with that."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8533800,
    "end": 8539800,
    "text": "Other questions on the futures agenda portion of this."
  },
  {
    "speaker": "Councilmember Stacy R. Hall",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8545960,
    "end": 8546600,
    "text": "Okay."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8547240,
    "end": 8558200,
    "text": "If there's no more questions on that, then we will look for council comments starting with the city manager."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8559580,
    "end": 8605350,
    "text": "Yeah, I will just reinforce our event on the 16th here in chambers at 6 o'. Clock. A few ways to participate remote in person and so and just watching on cable if you. If you so desire. So we look forward to engaging public around the fiscal year budget and as you know, most of our work has been around that. Look forward to over the next couple weeks engaging with council, answering questions. To Councilmember McQuillan's comment earlier, we're thankful to council. At the risk of sounding gratuitous, you presented a lot of challenges, a lot of questions, a lot of good food for thought relative to this process. Look forward to a little more of that over the next couple weeks and certainly help us and inform the process as we move forward. So thank you very much."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8606310,
    "end": 8608550,
    "text": "Council member McQuillan comments."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8609600,
    "end": 8769510,
    "text": "Thank you. Yes, thank you. April is always an energizing time in our city. Our parks are full, our neighborhoods are active. There's a real sense of connection across the city that reflects the strength of this community. With early voting underway and a statewide amendment on the ballot next week, I encourage residents to stay informed and participate. Engagement at every level is what keeps our democracy strong at the city level. We're deep in budget season and These are some of the most important decisions we make all year. Right now, we are focused on ensuring strong support for our schools, maintaining public safety services, and investing responsibly in infrastructure that residents rely on every day. That includes continued coordination through our shared services partnership with Fairfax county, ongoing investments in roadway and pedestrian safety, and critical stormwater infrastructure projects that help protect our neighborhoods long term. We've also continued to support accessible public transportation through our fare free Q bus system while working through ongoing discussions around housing and affordability to help ensure Fairfax City remains a place where people can live, work and stay. This month also invites us to reflect on our environment, and I'm proud of the continued focus on protecting our green spaces, improving resilience, and ensuring we are planning thoughtfully for the future of this city. With that, I'd also like to congratulate the women of influence that received her award this evening. Katie Johnson, congratulations. Thank you for all you've done for our community. I'd also like to just point out, though, what guides my work most are the conversations I have with our residents. Whether it's concerns about safety, affordability or overall quality of life, I deeply value all of those perspectives. They directly shape how I approach the work we do here. I also want to recognize how important it is that everyone in our community, especially students and families, feel supported and safe, and that there's confidence in coming forward when something is wrong. This month, as we observe Sexual Assault Awareness Month, that message feels especially meaningful and timely. It's a reminder of the importance of fostering a community where individuals feel heard, respected and protected, and where speaking up is met with support and care. I want to close by sincerely thanking everyone who has taken the time to reach out, share your thoughts and engage in these conversations that participation matters. It's democracy at work and I truly value it."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8769750,
    "end": 8772390,
    "text": "Thank you, Council Member Bates."
  },
  {
    "speaker": "Councilmember Anthony T. Amos",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8773650,
    "end": 8783090,
    "text": "I want to second the comments in support of Survivors of Sexual assault in recognition of Sexual Assault Awareness Month."
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8783090,
    "end": 8786210,
    "text": "Thank you, Council Member Peterson."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8786370,
    "end": 8850010,
    "text": "I wanted to share a personal health note, really, as a part of just general awareness to help everybody. So it's sort of a funny thing, you know, after you turn 65, suddenly your doctors start spending a lot more time paying attention to you and they start running you through all kinds of tests that you probably should have been doing like 25 years earlier. And it's like, oops, you know, so interesting process, takes a little time, just heads up. But I ended up as a part of that, having a sleep test and finding out that I had sleep apnea. And for those of you who don't know. It means you stop breathing while you're sleeping, which is not exactly a great thing to do. And there's various levels. I have what's known as moderate sleep apnea, which means, technically, between 15 and 30 times an hour, you stop breathing. And in my case, it's 17. And while that may not seem like a big deal, it adds up. So you could end up losing a couple hours of sleep every night from that. I mean, the average in terms of how much people sleep."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 8850240,
    "end": 9113080,
    "text": "Stop breathing for a moderate is not that long, 10 to 20 seconds, but for some of us, it's a whole lot longer. For me, it's between 55, 0 and 130 seconds per episode when I stop breathing. So, you know, you get a little bit tired the next day if you're trying to get to sleep like that. So the bad news is that. But the good news is it's eminently treatable. It's very easy to get a sleep test. It's just take it home, you do it, it's not a problem. And the remedy for it, if you have apnea is to wear a sleep mask. I do that. And what a game changer. I can't say that I'm leaping tall buildings, but pretty close to it. It really has been a complete game changer. One of the things I learned is that people are apparently really good about detecting acute fatigue, really terrible about detecting chronic fatigue until you've gotten over it. It's like, oh, my God, I can't believe all this time I did that. So I would encourage everybody, if you haven't already, to seriously consider getting a sleep test. And don't wait until you're 65. My doctor says you need to be doing this at 40 and go tell your insurance company, you know, to take care of you and do that. And there's a lot of things in that category, so I would heartily recommend it again. Easy to do. The thing to be aware of also is it can be lethal. And so, unfortunately, my family has friends and relations who didn't survive these episodes that took place at night. So it's serious business. The other thing just to be aware of is that it can catch up with you if you don't treat it at pretty inconvenient times. So somebody in our family, no names mentioned, fell asleep at a stoplight and the person behind him thought he was texting, right? So came up and knocked on the window, which is a good thing. Said, dude, what are you doing here? And he was like, snoring. So you should try to protect yourself. But just remember, we share the roads and we need to protect each other, too. So we have a responsibility in our personal health to avoid health impacts to other people at the same time. So it's just one more reason to do this. And I would reach back also to the earlier conversation we had about health care. We're very fortunate this area has, bar none, the best health care anywhere. We are really, really fortunate to live in an area that has the kind of advanced, accessible health care, we do, but it comes at a price. Not everybody can get access. And we'll talk a bit more about the Willard Sherwood center and the health center there. But public health is an incredibly part of our system. But then the commercial health care system and the insurance based system as well. But it's not equally accessible to everybody. And this is a pretty tough time right now because we haven't gotten reimbursements for Obamacare. A lot of people simply don't know what they're going to do. We do hear a lot of people saying they're making very hard choices about funding their health care and getting groceries, things like that. And those are really for real conversations that I think we need to internalize and appreciate as we go through what we can do here in the city to take care of all these things. So the other thing I would just say based on our earlier discussion this evening is I would like, I think a resolution here that would be quite timely and constructive would be for the city attorney to come back to us at some time in the not too distant future with a recommendation on how we might put in place a conflicts of interest policy that would deal with the potential for family conflicts related to slots that are under consideration for appointments. I think this is done rather commonly and probably standard templates for that. I think it'd be very helpful for us to be able to have a look at that and get the benefit of your advice on how that might be handled. I think it also would be very helpful for us to see what the options might be for us changing our holdover policy because it seems to have become a point of conflict and concern for the council. So I would hope that the committee would be open to, or the council rather would be open to having our attorney come back and provide us best advice in both of these areas. And let me just ask if there's anybody who doesn't agree with that"
  },
  {
    "speaker": "City Clerk",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 9114840,
    "end": 9115240,
    "text": "council."
  },
  {
    "speaker": "City Attorney",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 9115480,
    "end": 9118520,
    "text": "Mr. Lupkeman, appreciate the promotion."
  },
  {
    "speaker": "City Attorney",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 9120680,
    "end": 9160480,
    "text": "Just so I understand we have talked about with every council in the 20 years that I've been here about doing a code of ethics generally and councils have not adopted it. Are you all suggesting that we bring back a suggested code of ethics? We're certainly prepared to do that. We have the materials that we've updated year after year. Or are you suggesting bringing forward a one off related just to that discrete issue, which is a different thing but could be included in your policy with respect to boards and commissions, for example. I just want, I want to understand the tasking. I'm Sorry."
  },
  {
    "speaker": "Councilmember Tom Peterson",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 9160720,
    "end": 9235430,
    "text": "Well, sequentially the latter, but then ultimately the former. I mean, I think we're overdue having a code of ethics, but the proximate thing we need to deal with here is a conflict. We did not advance board and commission appointments tonight because of the distraction and, frankly, destabilization associated with the conflicts of interest issue. And I think that's a shadow that is cast over the whole appointment process that we need to remove the way the state has encouraged us to remove it through adherence of policy here. So that would be the first order of business to take care of that and then turn to the broader issue of the code of ethics. I would note that we all credit to you and to our city clerk for working very hard putting in place for the first time a board and commission handbook that covers many, many issues, including conflicts of interest. We, I think, recognize that was a work in progress. There were outstanding issues that would need to be updated and added to that. I think tonight's discussion underscores the urgency of doing that in key areas. And this is one of those areas that is urgent and needs to be done so that we can get back on track with our board and commission appointments, which at this stage are apparently frozen."
  },
  {
    "speaker": "City Attorney",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 9240310,
    "end": 9263450,
    "text": "So just looking at the calendar, considering you're in the middle of budget season, I would assume that perhaps the meeting or a couple meetings after budget adoption would be a good target for this discussion. And it will be a discussion because I assume there are differing views on this. But we'll be prepared to bring some information back at a. At a work session if. If that's the will of the council, happy to do it."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 9263450,
    "end": 9439630,
    "text": "We can. Yes. And we can look to the city manager to look at a futures list to put that discussion. Thank you, Council member Hardy Chandler. So, first of all, first of all, I want to acknowledge the civic connections kickoff that happened April 8th. Jennifer Rose and her curriculum trying to support residents and business owners to understand the inner workings of our city and come from an informed place and an engaged place, I think was second cohort. We even have alumni from the first cohort here. So it really is a program that I hope we can continue to support and rally around. So I was very honored to be there and to welcome that cohort. So thank you very much. I also want to highlight a very successful Home for Life Expo. I continue to be honored and impressed with being the liaison to the village and the city and to emphasize every time I get an opportunity that that is a working, very healthy, very dynamic advisory group. And the work that they do, not only for the city, but as a role model nationally, I think is really tremendous. My understanding is that the Home for Life attendees were significantly higher than last year. So continuing to expand access to resources and information for various people throughout our community. And I think that the benefits of that will go along beyond April 10th. I also want to acknowledge the Commission for Women event today. I was very honored to be a part of the commission during the time when the Woman of Influence Award was created, during my five year tenure on that commission. So I know that they do good work and really want to celebrate contributions to the community. Beyond that, I also want to just highlight, in spite of the discussion today, you know, part of being a servant is that you're going to work with people who have differences of opinion and express those differences. That's healthy. So I think that there was a dynamic discussion earlier and although we come from this, come to this with different perspectives, I was raised and will continue to respect everyone and that that respect comes through no matter whether there's agreement or disagreement. And I do believe that one of the aspects that would have prevented the discussion earlier or can prevent future."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 9440240,
    "end": 9462080,
    "text": "Conflicts is more expedient appointments, because I think that part of the delay contributed to the dynamic that that happened. But I really hope that we can get people on boards earlier. So with that, I'll just wrap up and, and appreciate it."
  },
  {
    "speaker": "City Manager/Staff",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 9462640,
    "end": 9693810,
    "text": "Council Member hall, thank you very much. I want to thank the county and our staff for putting on a great joint meeting last week. I don't think we had an opportunity with the work session to properly thank you all for doing that. I know there were a lot of questions that were answered and communication was really good. And it was nice to just have an open and upfront honest conversation, which I think was very, very helpful. I had a great time at my very first ever fire truck push in ceremony on Friday. I was very happy. I actually asked the question. I'm like, they're going to turn this on, right? Because otherwise, like, there's some older people here, somebody might hurt their back. I was feeling like risk management for a moment and they were like, we got this. It goes in reverse. It's all good. So it was fun. There were so many people there, I was barely able to touch part of the truck. But I did get to push, so that was very exciting. We had a great, great turnout. It was really, really great to see all these retired chiefs and all these other positions that have worked here for so long and now have gone off to retirement and come back and they just. There's such this camaraderie that you just see with firefighters and police too. And, you know, there's some, you know, finessing between the two departments, I think, too. You know, they rub each other in good ways, but it's just such a great group of people that just get together and just, they just exist and they all support each other and it was just, it was a really, really great opportunity for community, I'll say. There was an adorable little boy named Fireman Schultz, and he apparently was told to show up at 10am in order to be there for the push in. He got there 10 minutes early, but we had already pushed it in. And I felt terrible for this little boy. But I will say they all did a great job. They took pictures of him in front of the truck. But my heart went out to this little kid who clearly was. This was like the highlight of his month. So I am excited for the Women's Club of Fairfax fashion show on Saturday. There is Also on Sunday, April 19, a spring community cleanup at Van Dyke park starting at 9am I want to give a huge congratulations to Katie Johnson, who is still here to the bitter end for being our 2026 woman of influence recipient. And your time, your energy, your dedication, it is seen, it is recognized. And you are just an amazing resident here. And I think one of your greatest abilities is the ability to rally those around you. Right? Anybody can go out and pull weeds and do whatever, but you do it in such a way that makes people want to be a part of whatever organization or entity or group that you're working with. And you can find common ground with anybody on all of these different things. And it's just very, very spectacular and impressive to see. So thank you. I do also want to tell people that my campaign slogan when I ran was, this is your city and your opinion matters. And I wholeheartedly stand by that. And just as a reminder, you have two more weeks, essentially, to reach out to council, to send us questions, send us comments, let us know what you think about things. I hope you won't save it until the very last minute. So we're scrambling, you know, the morning of the 28th, but I do know that we also get to see many of you throughout our days and nights and, you know, the things that we're doing. So this will never be your last chance to have input on a budget. Right. It's a living document that kind of goes on and on. Yes, we set it for one year, but then we immediately move on to the next one. So I would strongly encourage you to attend the virtual or in person event on Thursday. I will certainly be there because we know budget's my jam. Right. I enjoy it. So thank you. And again, please, please, please continue to share your thoughts and ideas honestly on ways that we could do this whole thing better. So thank you, Council Member Amos."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 9694050,
    "end": 9864820,
    "text": "I would also extend that to remember, the noise ordinance is still open for discussion and comment until May 12, so keep that in mind. I'm going to apologize in advance. I wish I didn't have so many announcements, but I'll try to run through real quick. I want to echo the congratulations to Katie Johnson for your award. Very well deserved. I know that the county held an absolutely wonderful celebration for Michael Fry at the government center. I know. I saw the mayor there, former supervisor, who did a lot, especially when it comes to animal rights and protections, and has the animal shelter in the county named after him. So just wanted to echo our sentiments to his family and that he was such a phenomenal human being for everything he's done. Columbia was great. If y' all want to see pictures, just talk to me after or another day, because I know. Interesting night. I do want to share that tomorrow at Fairfax High School is the Hire a Lion Fair. I'm going to look at Jennifer Rose very sharply because it was really, really thanks to her. So I would love to thank the Fairfax Ford Foundation, Central Fairfax Chamber, City Schools. Dan Phillips and Maureen Kim came in so clutch on making this happen. My colleagues on the dais and all the businesses who signed up, we ended up hitting our max for businesses tomorrow. So it should be very solid turnout, good mix of folks. Wish I could have gotten in contact with Woody's Ice Cream, but I tried, I tried, but. So there should be 20 vendors there and it should be a really good time. Hope everyone can make it starting at 9:50am during Lion Time. Also excited to share Poetry Night for Spotlight on the Arts. I guess I kind of got put in charge of that for some reason. It's not my intention, but I kind of just fell into my lap and it's very well fitting for National Poetry Month. And I've always said that I, I feel like so much attention is given to the visual arts. I would love to see more emphasis on the literary arts. And now Sharon Chang has talked to all of us about that. But also excited to announce that we confirmed that Angelique Palmer, the Fairfax Poet Laureate, will be in attendance. So she will be headlining the event. So we're very excited to have her there. It will be Monday, April 27, starting at 6pm in the top section of Old Fire Station 3. So very excited for that. And then the last thing I will say is I just wanted to give a special thanks to Leadership Fairfax for honoring me with the 40 under 40 award earlier today. I have a weird feeling about awards. I greatly appreciate it. You know, starting off as a car salesman when I first got here and kind of being relatively unknown to where I am now, I just feel like I'm a culmination of everyone I've ever met. And I'm just eternally grateful for everyone I've met and those who came before me. And that's it."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 9866900,
    "end": 9868340,
    "text": "Councilmember Hardy Chandler."
  },
  {
    "speaker": "Councilmember Stacey D. Hardy-Chandler",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 9869140,
    "end": 9909770,
    "text": "Apologies, just one more follow up. I did want to acknowledge the celebration of the Educational and charitable foundation celebrating 25 years serving the Fairfax region. And that celebration, as always, offer scholarships to incredible students that definitely give you hope and optimism for the future. And I really appreciate the mayor coming to the event and doing a proclamation and acknowledgement of all of the work that the educational and charitable foundation does for our region. Really dedicated to community service. And also a great interview with an author but thank you Mayor for coming to that."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 9911700,
    "end": 9942990,
    "text": "So April, super busy month. Spotlight on the Arts got to talk about it because in 1985 our former mayor John Mason really put together Spotlight on the Arts. I think that it showed our commitment. We recently got an award for being one of the best small towns in America with our art scene. And Spotlight on the Arts has a number of events. The poetry event is one of them. The that council member Amos not only is apparently organizing the whole thing, but he is presenting there because council member Amos is a poet."
  },
  {
    "speaker": "Councilmember Stacy R. Hall",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 9944510,
    "end": 9945150,
    "text": "Own it."
  },
  {
    "speaker": "Mayor Catherine S. Read",
    "speaker_source": "manual_review",
    "speaker_source_detail": "Russ-verified council debate labels (PyAnnote behavioral mapping)",
    "start": 9946270,
    "end": 10000360,
    "text": "There's an event on Friday the 17th. There is a Spotlight on the Arts event. There is also the opening reception on April 24, which is the following Friday. But there are events for the rest of April and into the first part of May. So please check online for all of the events happening all over. Fairfax High School has their Rotten Tomatoes show at the high school and there's a lot of other events, music and theater going on in the next three weeks that celebrate the arts and is an important part of Spotlight on the Arts. So with that, I am now going to adjourn this meeting at 9:46pm on Tuesday. Sam."
  }
];

if (typeof module !== 'undefined' && module.exports) {
  module.exports = TRANSCRIPT_TURNS;
}
