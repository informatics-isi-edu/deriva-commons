// Configure deployment-specific data here

var chaiseConfig = {
    name: "Sample",
    layout: 'list',
    allowErrorDismissal: true,
    confirmDelete: true,
    headTitle: 'Chaise',
    customCSS: '/assets/css/chaise.css',
    navbarBrand: '/',
    navbarBrandImage: null,
    logoutURL: '/image-annotation',
    // signUpURL: '', The URL at a which a user can create a new account
    // profileURL: '', Globus deployments can use https://www.globus.org/app/account
    dataBrowser: '',
    maxColumns: 6,
    showUnfilteredResults: false,
    defaultAnnotationColor: 'red',
    feedbackURL: 'http://goo.gl/forms/f30sfheh4H',
    helpURL: '/help/using-the-data-browser/',
    showBadgeCounts: false,
    plotViewEnabled: false,
    recordUiGridEnabled: false,
    recordUiGridExportCSVEnabled: true,
    recordUiGridExportPDFEnabled: true,
    editRecord: true,
    deleteRecord: true,
    maxRecordsetRowHeight: 160,
    showFaceting: true,
    defaultCatalog: 12,
    resolverImplicitCatalog: 12,
    tour: {
      pickRandom: false,
      searchInputAttribute: "Data",
      searchChosenAttribute: "Data Type",
      searchInputValue: "micro",
      extraAttribute: "Mouse Anatomic Source",
      chosenAttribute: "Data Type",
      chosenValue: "Expression microarray - gene"
    },
    navbarMenu: {
        // The optional newTab property can be defined at any level. If undefined at root, newTab is treated as true
        // Each child menu item checks for a newTab property on itself, if nothing is set, the child inherits from it's parent.
        newTab: true,
        children: [
	    {
		"name" : "Search",
		"children" : [
		    {
			"name": "Collections",
			"url": "/chaise/recordset/#12/Data:Collection"
		    },
		    {
			"name": "Sequencing Data",
			"children" : [
			    {
				"name": "Studies",
				"url": "/chaise/recordset/#12/Data:Study"
			    },
			    {
				"name": "Experiments",
				"url": "/chaise/recordset/#12/Data:Experiment"
			    },
			    {
				"name": "Replicates",
				"url": "/chaise/recordset/#12/Data:Replicate"
			    },
			    {
				"name": "Files",
				"url": "/chaise/recordset/#12/Data:File"
			    }
			]
		    },
		    {
			"name": "Specimens",
			"url": "/chaise/recordset/#12/Data:Specimen"
		    }
		]
	    }
        ]
    },
    footerMarkdown: "This is a very simplified view of data from the RBK and GUDMAP projectsl **Please check** [Privacy Policy](/privacy-policy/){target='_blank'}",
    maxRelatedTablesOpen: 15,
};

if (typeof module === 'object' && module.exports && typeof require === 'function') {
    exports.config = chaiseConfig;
}
