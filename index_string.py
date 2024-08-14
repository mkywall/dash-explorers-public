index_string = '''
                        <!DOCTYPE html>
                        <html data-bs-theme="light" lang="en">
                        
                        <head>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0, shrink-to-fit=no">
                            <title>Crucible Data Platform</title>
                            <meta name="description" content="Crucible – named for the melting pot used in foundries of yore – is a unified data-management and computational system at the Molecular Foundry.">
                            {%metas%}
                            <link rel="icon" type="image/png" sizes="256x256" href="https://crucible.lbl.gov/assets/img/logo-256-white.png">
                            {%css%}
                            <link rel="stylesheet" href="https://crucible.lbl.gov/assets/bootstrap/css/bootstrap.min.css">
                            <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Montserrat:400,400i,700,700i,600,600i&amp;display=swap">
                            <link rel="stylesheet" href="https://crucible.lbl.gov/assets/css/baguetteBox.min.css">
                            <link rel="stylesheet" href="https://crucible.lbl.gov/assets/css/Banner-Heading-Image-images.css">
                            <link rel="stylesheet" href="https://crucible.lbl.gov/assets/css/Features-Large-Icons-icons.css">
                            <link rel="stylesheet" href="https://crucible.lbl.gov/assets/css/vanilla-zoom.min.css">
                        </head>
                        
                        <body>
                            <nav class="navbar navbar-expand-lg fixed-top bg-white clean-navbar navbar-light">
                                <div class="container"><a class="navbar-brand text-nowrap logo" href="#"><img width="64" height="64" src="https://crucible.lbl.gov/assets/img/logo-256-white.png" style="width: 64px;">Crucible Data Platform</a><button data-bs-toggle="collapse" class="navbar-toggler" data-bs-target="#navcol-1"><span class="visually-hidden">Toggle navigation</span><span class="navbar-toggler-icon"></span></button>
                                    <div class="collapse navbar-collapse" id="navcol-1">
                                        <ul class="navbar-nav ms-auto">
                                            <li class="nav-item"><a class="nav-link" href="../index.html">Home</a></li>
                                            <li class="nav-item dropdown"><a class="dropdown-toggle nav-link" aria-expanded="false" data-bs-toggle="dropdown" href="#">Services</a>
                                                <div class="dropdown-menu" data-bs-popper="none">
                                                 <a class="dropdown-item" href="https://boysenberry.dhcp.lbl.gov:5000/manage_data">Manage Data</a>
                                                  <a class="dropdown-item" href="https://mf-scicat.lbl.gov">SciCat Data Catalog</a>
                                                  <a class="dropdown-item" href="https://crucible.lbl.gov/dash/">Data Explorers</a>
                                                  <a class="dropdown-item" href="/analysis/">Data Analysis Workflows</a>
                                                  <a class="dropdown-item" href="/hpc/">HPC</a>
                                                  <a class="dropdown-item" href="/instruments/">Instruments</a>
                                            </li>
                                            <li class="nav-item dropdown"><a class="dropdown-toggle nav-link" aria-expanded="false" data-bs-toggle="dropdown" href="#">Software&nbsp;</a>
                                                <div class="dropdown-menu"><a class="dropdown-item" href="https://github.com/MolecularFoundry/">GitHub Project</a><a class="dropdown-item" href="http://www.scopefoundry.org">ScopeFoundry</a></div>
                                            </li>
                                            <li class="nav-item"><a class="nav-link" href="../about.html">About</a></li>
                                        </ul>
                                    </div>
                                </div>
                            </nav>
                            <main class="page">
                                <section class="clean-block about-us">
                                    <div class="container">
                                        <div class="block-heading">
                                            <h2 class="text-info"></h2>
                                            
                                        </div>
                                    </div>
                                    <section>
                                        {%app_entry%}
                                    </section>
                                    <div class="container"></div>
                                </section>
                            </main>
                            <footer>
                                <script src="https://crucible.lbl.gov/assets/bootstrap/js/bootstrap.min.js"></script>
                                <script src="https://crucible.lbl.gov/assets/js/baguetteBox.min.js"></script>
                                <script src="https://crucible.lbl.gov/assets/js/vanilla-zoom.js"></script>
                                <script src="https://crucible.lbl.gov/assets/js/theme.js"></script>
                        
                                {%config%}
                                {%scripts%}
                                {%renderer%}        
                            </footer>
                        
                        </body>
    
                    </html>
    
    
        '''