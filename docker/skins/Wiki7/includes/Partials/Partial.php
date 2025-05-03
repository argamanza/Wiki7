<?php
/**
 * Wiki7 - A responsive skin developed for the Star Wiki7 Wiki
 *
 * This file is part of Wiki7.
 *
 * Wiki7 is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Wiki7 is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Wiki7.  If not, see <https://www.gnu.org/licenses/>.
 *
 * @file
 * @ingroup Skins
 */

declare( strict_types=1 );

namespace MediaWiki\Skins\Wiki7\Partials;

use MediaWiki\Output\OutputPage;
use MediaWiki\Skins\Wiki7\GetConfigTrait;
use MediaWiki\Skins\Wiki7\SkinWiki7;
use MediaWiki\Title\Title;

/**
 * The base class for all skin partials
 * TODO: Use SkinComponentRegistryContext
 */
abstract class Partial {

	use GetConfigTrait;

	/** @var SkinWiki7 */
	protected $skin;

	/** @var OutputPage */
	protected $out;

	/** @var Title */
	protected $title;

	/** @var User */
	protected $user;

	/**
	 * Constructor
	 * @param SkinWiki7 $skin
	 */
	public function __construct( SkinWiki7 $skin ) {
		$this->skin = $skin;
		$this->out = $skin->getOutput();
		$this->title = $this->out->getTitle();
		$this->user = $this->out->getUser();
	}
}
