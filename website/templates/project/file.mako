<%inherit file="base.mako"/>
<%def name="title()">${file_name}</%def>
<%def name="content()">
<div mod-meta='{"tpl": "project/project_header.mako", "replace": true}'></div>

<div id='file-container' class="row">
    <div class="col-md-8">
      	<section>
          	<div class="page-header overflow">
              	<h1>${file_name} (current)</h1>
          	</div>
      	</section>
##        todo fix div id file-rendered to proper naming convention
        <div> <a href=${download_path}>Download latest version</a></div><br>
        <div id='fileRendered' class="mfr mfr-file">
      		${rendered}
      	</div>
        ##todo remove this and fix the bottom one...
    % if not is_rendered:
       <script> FileRenderer.start("${download_path}render", "#fileRendered");</script>
    % endif

    </div>
    <div class="col-md-4">
      	<ol class="breadcrumb">
            <li><a href="${node['url']}files/">${node['title']}</a></li>
  			<li class="active overflow" >${file_name}</li>
		</ol>
		<table class="table table-striped" id='file-version-history'>
			<thead>
				<tr>
					<th>Version</th>
					<th>Date</th>
                    <th>User</th>
					<th colspan=2>Downloads</th>
				</tr>
			</thead>
			<tbody>
            % for version in versions:
                <tr>
                    <td>
                        ${version['display_number']}
                    </td>
                    <td>
                        ${version['date_uploaded']}
                    </td>
                    <td>
                        <a href="${version['committer_url']}">${version['committer_name']}</a>
                    </td>
                    <td>
                        ${version['total']}
                    </td>
                    <td>
                        <a href="${node['api_url']}files/download/${file_name}/version/${version['number']}/"><i class="icon-download-alt"></i></
                    </td>
                </tr>
			%endfor
			</tbody>
		</table>
    </div>
</div>
</%def>
##todo fix this -ajs
##<%def name="javascript_bottom()">
##    % if not is_rendered:
##       <script> FileRenderer.start("${download_path}render");</script>
##    % endif
##</%def>



