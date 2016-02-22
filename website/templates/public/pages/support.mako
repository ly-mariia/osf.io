<%inherit file="base.mako"/>
<%def name="title()">Support</%def>

<%def name="stylesheets()">
    <link rel="stylesheet" href="/static/css/pages/support-page.css">
    <link rel="stylesheet" href="/static/css/pages/getting-started-page.css">

</%def>

<%def name="content()">
<div class="container">
    <h1> Support</h1>
    <div class="row m-t-md">
        <div class="col-sm-8 col-lg-9">
            <input type="text" class="form-control support-filter" placeholder="Search">
            <button class="btn btn-default clear-search">Clear Search</button>
            <button class="btn btn-default expand-all"> Expand All </button>
            <button class="btn btn-default collapse-all"> Collapse All </button>

            <div class="row">
                <div class="col-xs-12">
                    <h3> Frequently Asked Questions </h3>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> How much does the OSF service cost?</h5>
                            <p class="support-body">It's free!</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i cla`ss="fa fa-angle-right"></i> How can it be free? How are you funded?</h5>
                            <p class="support-body">The OSF is maintained and developed by the <a href="http://cos.io">Center for Open Science</a> (COS), a non-profit organization. COS is supported through grants from a variety of supporters, including <a href="http://centerforopenscience.org/about_sponsors/"> federal agencies, private foundations, and commercial entities</a>.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> What if you run out of funding? What happens to my data?</h5>
                            <p class="support-body">Data stored on the OSF is backed by a $250,000 preservation fund that will provide for persistence of your data, even if the Center for Open Science runs out of funding. The code base for the OSF is entirely <a href="https://github.com/CenterForOpenScience/osf.io">open source</a>, which enables other groups to continue maintaining and expanding it if we aren’t able to.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> How will the OSF be useful to my research?</h5>
                            <p class="support-body">The OSF integrates with the scientist's daily workflow. The OSF helps document and archive study designs, materials, and data. The OSF facilitates sharing of materials and data within a laboratory or across laboratories. The OSF also facilitates transparency of laboratory research and provides a network design that details and credits individual contributions for all aspects of the research process. To see how it works, watch our short <a href="/getting-started">Getting Started</a> videos, see the <a href="https://osf.io/4znZP/wiki/home">OSF Features</a> page, or see how other scientists <a href="https://osf.io/svje2/">use the OSF.</a></p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> How can I help develop the OSF?</h5>
                            <p class="support-body">If you are a developer, check out the source code for the OSF <a href="https://github.com/CenterForOpenScience/osf.io">on GitHub</a>.
                            The <a href="https://github.com/CenterForOpenScience/osf.io/issues">issue tracker</a> is a good place to find ways to help. For more information, send an email to <a
                            href="mailto:contact@osf.io">contact@osf.io</a>.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> What is coming to the OSF?</h5>
                            <p class="support-body">For updates on new features, you can join our <a href="https://groups.google.com/forum/#!forum/openscienceframework">Google
                            Group</a>, find us on <a href="https://twitter.com/osframework">Twitter</a> and on <a href="https://www.facebook.com/OpenScienceFramework">Facebook</a>, or follow the COS <a href="https://github.com/centerforopenscience">GitHub</a> page.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> How can I contact the OSF team if I have a question that the FAQ or Getting Started pages don’t answer?</h5>
                            <p class="support-body">Send us an <a href="mailto:support@osf.io">email</a> and we'll be happy to help you.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> How can I get started on using the OSF?</h5>
                            <p class="support-body">OSF membership is open and free, so you can
                                just register and check out our <a href="/getting-started">Getting Started</a>
                                page for a thorough run-down of how it works. This FAQ page will only cover a few of the most basic questions about the OSF, so it’s highly recommended that you read through Getting Started if you have any issues.</p>
                        </div>                         
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> How do I create a lab group/organizational group?</h5>
                            <p class="support-body">The best way to create a lab or organizational group on the OSF is to create a project for that group. Then, individual projects within the lab can either be organized into components of the lab project or into their own projects which are linked to the lab group project. For an example, check out the <a href="https://osf.io/ezcuj/">Reproducibility Project: Psychology.</a></p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> What services can I use with the OSF?</h5>
                            <p class="support-body">The OSF supports many third-party add-ons. For storage, you can connect to Amazon S3, Box, Dataverse, Dropbox, Figshare, Github, and Google Drive, and the OSF has its own default storage add-on, OSF Storage, if you choose not to connect to any third-party add-ons. The OSF also supports Mendeley and Zotero as citation managers. Please refer to the helpful <a href="/getting-started/#addons">Add-ons section</a> of our Getting Started page for more information on how to use add-ons.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> What can I do with a file after uploading it into a storage add-on?</h5>
                            <p class="support-body">You can view, download, delete, and rename any files uploaded into OSF Storage. Files in third party storage add-ons might have restrictions on renaming and downloading.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> What is a registration?</h5>
                            <p class="support-body">A registration is a frozen version of your project that can never be edited or deleted, but you can issue a retraction of it later, leaving behind basic metadata. When you create the registration, you have the option of either making it public immediately or making it private for up to four years through an embargo. A registration is useful for certifying what you did in a project in advance of data analysis, or for confirming the exact state of the project at important points of the lifecycle, such as manuscript submission or the onset of data collection.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> What if I don't want to register anything in the OSF?</h5>
                            <p class="support-body">Registering is an optional feature of the OSF.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> What is the cap on data per user?</h5>
                            <p class="support-body">There is a limit on the size of individual files uploaded to the OSF. This limit is 5 GB. If you have larger files to upload, you might consider utilizing add-ons. When archiving files during the registration process, there is a 1 GB total limit across all storage add-ons being archived.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> How do I get a DOI or ARK for my project?</h5>
                            <p class="support-body">DOIs and ARKs are available for <b>public registrations</b> of projects. To get a DOI or ARK for your project, first create a registration of your project, and make sure the registration is public. Then click the "Create DOI / ARK" link, located in the block of text below the project title. A DOI and ARK will be automatically created. </p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> What if I don't want to make anything available publicly in the OSF?</h5>
                            <p class="support-body">
                                The OSF is designed to support both private and public workflows. You can
                                keep projects, or individual components of projects, private so that only
                                your project collaborators have access to them.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> How secure is my information?</h5>
                            <p class="support-body">Security is extremely important for
                                the OSF. When you sign up and create a password, your password is not
                                recorded. Instead, we store a <a href="http://bcrypt.sourceforge.net/">bcrypt
                                    hash</a> of your password. This is a computation on your password that
                                cannot be reversed, but is the same every time it is computed from your
                                password. This provides extra security. No one but you can know your
                                password. When you click "Forgot your password," the OSF sends you a new random
                                password because it neither stores nor has the ability to compute your password.
                                <br/><br/>
                                Data and materials posted on the OSF are not yet encrypted, unless you encrypt
                                them before uploading to the site. This means that if our servers were
                                compromised, the intruder would have access to raw data. While we have taken
                                technological measures to minimize this risk, the level of security can be
                                improved further. We will offer encryption soon, and we will partner with
                                data storage services that offer strong security features.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> Is the OSF HIPAA compliant?</h5>
                            <p class="support-body">You should refer to your institutional policies regarding specific security requirements for your research.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> How can I license my data/code/etc.?</h5>
                            <p class="support-body">To apply a license to your OSF project, visit the project's overview page and select one from the "License picker," below the project's description. You can select from a variety of commonly used licenses or upload your own.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> How does the OSF store and backup files that I upload to the site?</h5>
                            <p class="support-body">The OSF stores files with <a href="http://www.rackspace.com/">Rackspace</a>
                                via an open source sponsorship, and has backups on
                                <a href="http://aws.amazon.com/glacier/">Amazon's Glacier platform</a>.
                                The OSF maintains several backup schemes, including off-site backups and
                                automated backups performed by our host every day, week, and fortnight.</p>
                            <p class="support-body">Rackspace and Amazon Glacier have their own methods to support data integrity (e.g., redundancy across 5+ locations), but the Open Science Framework takes the extra step of calculating multiple <a href="https://en.wikipedia.org/wiki/Checksum">checksums</a> and <a href="https://en.wikipedia.org/wiki/Parchive">parity archives</a> to account for even the most improbable errors.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> What do I do if I lost my email confirmation for OSF registration, or I never received it?</h5>
                            <p class="support-body">Log into the OSF with the email address and password of the account you created, and there will be a link to resend the confirmation email.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> My email address has changed. How do I change my login email?</h5>
                            <p class="support-body">From your <a href="/settings/account">account settings</a> page, you can add additional email addresses to your account, and select which of these is your primary email address. Any of these emails can be used to log in to the OSF. </p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> I have multiple OSF accounts. How do I merge them into one account?</h5>
                            <p class="support-body">Log into the account you wish to keep and navigate to your <a href="/settings/account/">account settings</a> page. There, enter the email address associated with your other OSF account. You will receive a confirmation link via email. Clicking the link will merge the projects and components into one account.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> How do I deactivate my OSF account?</h5>
                            <p class="support-body">From your <a href="/settings/account/">account settings</a> page, you can request a deactivation of your OSF account. A member of the OSF team will review your request and respond to confirm deactivation.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> What is the difference between a component and a folder?</h5>
                            <p class="support-body">A folder can be used to organize files within a project or component - just like a folder on your own computer groups files together. A component is like a sub-project to help you organize different parts of your research. Components have their own privacy and sharing settings as well as their own unique, persistent identifiers for citation, and their own wiki and add-ons. You can also register a component on its own, without registering the parent project.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> How do I delete a project or component?</h5>
                            <p class="support-body">To delete a project or component, navigate to the project or component and click on "Settings" in the gray navigation bar. There you will see a red "delete" button. You can only delete a project or component that does not contain other components, so you must delete any nested components first.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> How do I move a file from one storage add-on to another? Or one component to another?</h5>
                            <p class="support-body">You can move files between components and add-ons, provided the components and add-ons are a part of the same project, by simply dragging and dropping from within the files widget of the project overview page or the Files tab. The Dataverse add-on does not currently support this feature.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> How do I rename a project?</h5>
                            <p class="support-body">You can rename a project or a component by clicking on the project title in the project or component overview page.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> I’m using the search function in the top navigation bar to find one of my projects, but it’s not showing up in the results. What’s wrong?</h5>
                            <p class="support-body">The search function only returns public projects, so if you’re searching for one of your own private projects, it won’t be returned in the results. To search for your own projects, go to your dashboard, and use the “Go to my project” widget on the top right.</p>
                        </div>
                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> I have a DOI for my project on the OSF, but I've decided I'd rather host the material elsewhere. How can I do this without losing/needing a new DOI?</h5>
                            <p class="support-body">Send us an email with your DOI and the new location of your materials and we'll update the URL associated with your DOI. </p>
                        </div>


                        <!-- Getting Started -->
                    <h3> Getting Started with OSF </h3>

                        <div class="support-item m-t-lg">
                            <h5 class="support-head f-w-xl"><i class="fa fa-angle-right"></i> Use projects to organize your work</h5>
                            <p class="support-body">The OSF organizes your lines of research into projects. Projects come with features meant to streamline
                            your workflow as well as make your work more discoverable.

                                        <div class="gs-video embed-responsive embed-responsive-16by9" style="max-width: 102%; width: 102%;">
                                               <!--  Max width for this video adjusted because of black border -->
                                            <div class="embed-responsive-item youtube-loader" id="2TV21gOzfhw"></div>
                                        </div>

                            </p>

                        </div>




                        <h3 class="text-center anchor">Collaborate with your colleagues</h3>
                        <p>Keep yourself and your collaborators on point while collecting data by using the OSF. Add
                            contributors to your project so that everyone has access to the same files. Use our pre-formatted
                            citations and URLs to make sure credit is given where credit is due.  </p>
                        <div class="row">
                            <div class="col-md-10 col-md-offset-1">
                                <div class="gs-video embed-responsive embed-responsive-16by9">
                                    <div class="embed-responsive-item youtube-loader" id="UtahdT9wZ1Y"></div>
                                </div>
                            </div>
                        </div>

                                    <h3 class="text-center anchor">Simplify your life with version control</h3>
                                    <p>Keep your research up to date by uploading new versions of documents to the OSF. We use version
                                        control to keep track of older versions of your documents so you don't have to. You can also register
                                        your work to freeze a version of your project.</p>
                                    <div class="row">
                                        <div class="col-md-10 col-md-offset-1">
                                            <div class="gs-video embed-responsive embed-responsive-16by9">
                                                <div class="embed-responsive-item youtube-loader" id="ZUtazJQUwEc"></div>
                                            </div>
                                        </div>
                                    </div>

                                <h2 class="text-center">Structuring your work</h2>
                                <div class="col-md-12">
                                    <%include file="/public/pages/help/organizer.mako"/>
                                    <%include file="/public/pages/help/dashboards.mako"/>
                                    <%include file="/public/pages/help/user_profile.mako"/>
                                    <%include file="/public/pages/help/projects.mako"/>
                                    <%include file="/public/pages/help/components.mako"/>
                                    <%include file="/public/pages/help/files.mako"/>
                                    <%include file="/public/pages/help/links.mako"/>
                                    <%include file="/public/pages/help/forks.mako"/>
                                    <%include file="/public/pages/help/registrations.mako"/>
                                    <%include file="/public/pages/help/wiki.mako"/>
                                </div>

                                <h2 class="text-center">Sharing your work</h2>
                                <div class="col-md-12">
                                    <%include file="/public/pages/help/contributors.mako"/>
                                    <%include file="/public/pages/help/privacy.mako"/>
                                    <%include file="/public/pages/help/licenses.mako"/>
                                    <%include file="/public/pages/help/citations.mako"/>
                                    <%include file="/public/pages/help/view_only.mako"/>
                                    <%include file="/public/pages/help/comments.mako"/>
                                </div>

                                <h2 class="text-center m-b-lg">OSF Add-ons</h2>
                                <div class="col-md-12">
                                    <%include file="/public/pages/help/addons.mako"/>
                                </div>

                                <h2 class="text-center">Metrics</h2>
                                <div class="col-md-12">
                                    <%include file="/public/pages/help/statistics.mako"/>
                                    <%include file="/public/pages/help/notifications.mako"/>
                                </div>




                </div>
            </div>
        </div>
        <div class="col-sm-4 col-lg-3 support-sidebar">
            <h4 class="f-w-lg">Get in Touch</h4>
            <p> For emails about technical support:</p>
            <p> support@cos.io</p>
            <p> For all other questions or comments: </p>
            <p>contact@cos.io</p>
            <h4 class="f-w-xl"> Do you have Prereg Challenge related questions? </h4>
                <p>Check out our [Prereg section] on the cos.io website. </p>
            <h4 class="f-w-xl"> Are you looking for statistics consultations?</h4>
                <p>COS provides statistics consulation for free. To learn more about this service visit the [COS statistics consulting pages].</p>

            <h4 class="f-w-xl"> Other ways to get help </h4>
            <button class="btn btn-sm btn-default"> Ask us a question on twitter </button>
            <button class="btn btn-sm btn-default"> Join our mailing list </button>
            <button class="btn btn-sm btn-default"> Follow us on Facebook </button>

        </div>
    </div>
</div>
<script src=${"/static/public/js/support-page.js" | webpack_asset}></script>

</%def>
